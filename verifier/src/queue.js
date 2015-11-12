'use strict';

const Firebase = require('firebase');
const FirebaseTokenGenerator = require('firebase-token-generator');
const uuid = require('node-uuid');
const FIFO = require('./fifo').FIFO;
const verifier = require('./verifier');
const events = require('events');

const DEFAULT_PRESENCE_DELAY = 30000;
const DEFAULT_MAX_WORKER = 10;


class Queue extends events.EventEmitter {

  constructor(endpoint, dockerClient, options) {
    super();

    this.endpoint = endpoint;
    this.ref = new Firebase(endpoint);
    this.queueName = this.ref.key();
    this.taskRef = this.ref.child('tasks');
    this.workerRef = this.ref.child('workers');
    this.dockerClient = dockerClient;

    this.tasksToRun = new FIFO();
    this.taskRunning = 0;

    this.authData = undefined;

    this.ref.onAuth(authData => {
      this.authData = authData;

      if (authData && authData) {
        this.emit('loggedIn', authData);
      } else {
        this.emit('loggedOut', authData);
      }
    });

    this.opts = Object.assign({
      presenceDelay: DEFAULT_PRESENCE_DELAY,
      maxWorker: DEFAULT_MAX_WORKER
    }, options || {});

  }

  get isLoggedIn() {
    return this.authData && this.authData.uid;
  }

  get isWorker() {
    return (
      this.isLoggedIn &&
      this.authData.auth &&
      this.authData.auth.isWorker &&
      this.authData.auth.queue === this.queueName
    );
  }

  /**
   * Authenticate the firebase client with the custom token.
   *
   * Note only one firebase client per process. You cannot use two firebase
   * client with different token.
   *
   * @param  {string}  token
   * @return {Promise}
   */
  auth(token) {
    return new Promise((resolve, reject) => {
      this.ref.authWithCustomToken(token, (err, authData) => {
        if (err) {
          reject(err);
        } else {
          this.authData = authData;
          resolve(authData);
        }
      });
    });
  }

  /**
   * Push a new task to the firebase queue.
   *
   * To use for developpment.
   *
   * @param  {object}  payload Verification request
   *                           (should include a language, a solution and a test)
   * @return {Promise}         Promise resolving to the new task reference.
   */
  pushToQueue(payload) {
    if (!this.isLoggedIn) {
      return Promise.reject(new Error('No user logged in.'));
    }

    return promisedPush(this.taskRef, {
      started: false,
      completed: false,
      archived: false,
      owner: this.authData.uid,
      payload: payload
    });
  }

  /**
   * Register a worker for a queue and start a timer to update the worker
   * presence.
   *
   * @return {Promise} Resolve when the worker is registered, to a function to
   *                   deregister it.
   */
  registerWorker() {
    if (!this.isWorker) {
      return Promise.reject(new Error('The user is not logged in as a worker for this queue'));
    }

    return promisedSet(this.workerRef.child(this.authData.uid), {
      startedAt: Firebase.ServerValue.TIMESTAMP,
      presence: Firebase.ServerValue.TIMESTAMP
    }).then(ref => {
      this.emit('workerRegistered', ref);

      let timer, stopTimer;

      timer = setInterval(() => {
        this.updatePresence().catch(stopTimer);
      }, this.opts.presenceDelay);

      stopTimer = () => {
        if (timer !== undefined) {
          clearInterval(timer);
          timer = undefined;
          this.emit('workerPresenceUpdateStopped');
        }
      };

      return () => {
        stopTimer();

        if (!this.isWorker) {
          return Promise.reject(new Error('The user is not logged in as a worker for this queue'));
        }

        return promisedSet(ref, null).then(() => this.emit('workerRemoved', ref));
      };
    });
  }

  /**
   * Update the worker presence.
   *
   * @return {Promise} Resolve when the presence is updated
   */
  updatePresence() {
    if (!this.isWorker) {
      return Promise.reject(new Error('The user is not logged in as a worker for this queue'));
    }

    return promisedSet(
      this.workerRef.child(this.authData.uid).child('presence'),
      Firebase.ServerValue.TIMESTAMP
    ).then(
      () => this.emit('workerPresenceUpdated')
    ).catch(err => {
      this.emit('workerPresenceUpdateFailed', err);
      return Promise.reject(err);
    });
  }

  /**
   * Start watching the task queue and running opened tasks and any new task
   * added later.
   *
   * Returns a promise resolving when the worker is registered. It will resolve
   * to a fn that will stop the watch when called. Note that you do not it to
   * call it the auth token expire.
   *
   * It will reject if the worker couldn't register itself.
   *
   * To deal with Auth token expiring, you should listen for "watchStopped"
   * event and then restart watching with a new token.
   *
   * TODO:
   * - remove claimed event.
   *
   * @return {Promise}
   */
  watch() {
    this.tasksToRun = new FIFO();

    return this.registerWorker().then(deregister => {
      let cancel;

      const ref = this.taskRef.orderByChild('started').equalTo(false);
      const eventHandler = ref.on(
        'child_added',
        snapshot => this.sheduleTask(snapshot.key(), snapshot.val()),
        err => {
          this.emit('watchStopped', err);
          return deregister();
        }
      );

      cancel = () => {
        ref.off(eventHandler);
        this.emit('watchStopped');
        return deregister();
      };

      this.emit('watchStarted', ref, cancel);
      return cancel;
    });
  }

  /**
   * Schedule run of a new task.
   *
   * The task will be run immedialy or enqueue if if there are to many concurent
   * task running.
   *
   * @param  {string} key  Task id
   * @param  {Object} data Task body
   */
  sheduleTask(key, data) {
    this.tasksToRun.push({key, data});
    this.emit('taskRunScheduled', key, data);

    if (this.taskRunning >= this.opts.maxWorker) {
      return;
    }

    this.runTask(this.tasksToRun.shift());
  }

  /**
   * Async. run a task until the queue is empty.
   *
   * @param  {Object} task Task key and body.
   * @return {Promise}     Resolve when the queue is empty.
   */
  runTask(task) {
    if (!task) {
      return Promise.resolve();
    }

    const skip = {};

    this.taskRunning++;
    return this.claimTask(task).catch(
      () => Promise.reject(skip)
    ).then(
      () => verifier.run(this.dockerClient, task.data.payload)
    ).then(results => {
      this.emit('taskRun', task.key, results);
      return this.saveTaskResults(task, results);
    }).catch(err => {
      if (err === skip) {
        return;
      }

      this.emit('taskRunFailed', task.key, err);
      return this.removeTaskClaim(task);
    }).then(
      // Regardless of promise settlement, recover and decrease task running count.
      () => this.taskRunning--,
      () => this.taskRunning--
    ).then(
      () => this.run(this.tasksToRun.shift())
    );

  }

  /**
   * Claim a task.
   *
   * Resolve when the task is claimed.
   *
   * @param  {Object} task Task key and body.
   * @return {Promise}     Resolve when the
   */
  claimTask(task) {
    if (!this.isWorker) {
      return Promise.reject(new Error('The user is not logged in as a worker for this queue'));
    }

    return promisedUpdate(this.taskRef.child(task.key), {
      worker: this.authData.uid,
      started: true,
      startedAt: Firebase.ServerValue.TIMESTAMP
    }).then(
      () => this.emit('taskClaimed', task.key)
    ).catch(err => {
      this.emit('taskClaimFailed', task.key, err);
      return Promise.reject(err);
    });
  }

  /**
   * Remove claim on a task
   *
   * @param  {Object} task Task key and body
   * @return {Promise}     Resolve when claim is removed.
   */
  removeTaskClaim(task) {
    if (!this.isWorker) {
      return Promise.reject(new Error('The user is not logged in as a worker for this queue'));
    }

    return promisedUpdate(this.taskRef.child(task.key), {
      worker: null,
      started: false,
      startedAt: null
    }).then(
      () => this.emit('taskClaimRemoved', task.key)
    ).catch(err => {
      this.emit('taskClaimRemovalFailed', err);
      return Promise.reject(err);
    });
  }

  /**
   * Save task result to firebase DB.
   *
   * @param  {Object} task    Task key and body.
   * @param  {Object} results Task result.
   * @return {Promise}        Resolve when result is saved.
   */
  saveTaskResults(task, results) {
    if (!this.isWorker) {
      return Promise.reject(new Error('The user is not logged in as a worker for this queue'));
    }

    return promisedUpdate(this.taskRef.child(task.key), {
      results: results,
      completedAt: Firebase.ServerValue.TIMESTAMP,
      completed: true
    }).then(
      () => this.emit('taskResultSave', task.key)
    ).catch(err => {
      this.emit('taskResultSavingFailed', err);
      return Promise.reject(err);
    });
  }

  /**
   * Remove any claim on the task in the queue and reset it.
   *
   * TODO: remove old client and old claim.
   *
   * @return {Promise}.
   */
  cleanUp() {
    if (!this.isWorker) {
      return Promise.reject(new Error('The user is not logged in as a worker for this queue'));
    }

    this.tasksToRun.reset();
    return Promise.resolve();
  }

}

/**
 * Singpath Task queue
 * @param  {string} endpoint Full firbase URL to a SingPath queue.
 * @return {Queue}
 */
exports.queue = (endpoint, dockerClient) => new Queue(endpoint, dockerClient);

/**
 * Return a auth token generator.
 *
 * @param  {string} secret Firebase db secret.
 * @return {object}
 */
exports.tokenGenerator = function tokenGenerator(secret) {
  const generator = new FirebaseTokenGenerator(secret);

  return {
    /**
     * Generate a custom auth token for a user
     *
     * @param  {string} uid Optional user uid.
     * @return {string}     Auth token
     */
    user: (uid) => generator.createToken({uid: uid || uuid.v4(), isUser: true}),

    /**
     * Generate a custom auth token for verifier worker.
     * @param  {string} queueName Queue name the worker is allow to work on.
     * @return {[type]}           [description]
     */
    worker: (queueName) => generator.createToken({uid: uuid.v4(), isWorker: true, queue: queueName})
  };
};


function promisedPush(ref, data) {
  try {
    return promisedSet(ref.push(), data);
  } catch (e) {
    // in case ref.push throw.
    return Promise.reject(e);
  }
}

function promisedSet(ref, data) {
  return new Promise((resolve, reject) => {
    ref.set(data, err => {
      if (err) {
        reject(err);
      } else {
        resolve(ref);
      }
    });
  });
}

function promisedUpdate(ref, data) {
  return new Promise((resolve, reject) => {
    ref.update(data, (err) => {
      if (err) {
        reject(err);
      } else {
        resolve(ref);
      }
    });
  });
}
