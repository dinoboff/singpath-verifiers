'use strict';

const Docker = require('dockerode');
const fs = require('./promiseFs');
const Writable = require('stream').Writable;
const images = require('./images.json');

const DELAY = 6000;
const SOCKET_PATH = '/var/run/docker.sock';
const VERIFIERS_TAG = 'latest';


/**
 * Return a Promise resolving to a dockerode client.
 *
 * @return {Promise}
 */
exports.dockerClient = function dockerClient() {
  return fs.pathExist(SOCKET_PATH).then(socketPath => new Docker({socketPath}));
};

/**
 * Writeable stream collecting verifier sdtout stream.
 *
 */
class Response extends Writable {

  constructor(container, stream) {
    super({});
    this.buffer = new Buffer('');

    stream.on('end', () => {
      this.end();
    });

    container.modem.demuxStream(stream, this, process.stderr);
  }

  _write(chunk, encoding, callback) {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    callback();
  }

  toString() {
    return this.buffer.toString('utf8');
  }

  parse() {
    return JSON.parse(this.toString());
  }
}

/**
 * Error holding refrence to the container the error relate to.
 *
 */
class VerifierError extends Error {

  constructor(msg, verifier) {
    super(msg);
    this.verifier = verifier;
  }

}

/**
 * Wrapper over dockerode container methods returning Promises
 *
 */
class Verifier {

  /**
   * Verifier constructor
   *
   * @param  {dockerode.Container} container A container with TTY set to false.
   * @return {Verifier}              [description]
   */
  constructor(container) {
    this.container = container;
    this.out = undefined;
  }

  _wrapWithData(meth) {
    const args = Array.from(arguments).slice(1);

    return new Promise((resolve, reject) => {
      meth.apply(this.container, args.concat((err, data) => {
        if (err) {
          reject(new VerifierError(err, this));
        } else {
          resolve(data);
        }
      }));
    });
  }

  _wrap() {
    return this._wrapWithData.apply(this, arguments).then(() => this);
  }

  /**
   * Attach a stream collecting the container stdout into a buffer.
   *
   * @return {Promise} Resolve to the verifier once the the container is
   *                   attached.
   *
   */
  attach() {
    return this._wrapWithData(this.container.attach, {stream: true, stdout: true, stderr: true}).then(stream => {
      this.out = new Response(this.container, stream);
      return this;
    });
  }

  /**
   * Start the container.
   *
   * @return {Promise} Resolve to the verifier once the the container is started.
   */
  start() {
    return this._wrap(this.container.start, {});
  }

  /**
   * Wait for the container to stop for up to the delay argument (in ms).
   *
   * @param  {number} delay
   * @return {[type]}       Resolve when the container stop or reject when the
   *                        delay timeout, which ever first.
   */
  wait(delay) {
    return new Promise((resolve, reject) => {
      let hasTimedOut = false;

      const to = setTimeout(() => {
        hasTimedOut = true;
        reject(new VerifierError('Timeout', this.container));
      }, delay);

      this.container.wait((err) => {
        if (hasTimedOut) {
          return;
        } else {
          clearTimeout(to);
        }


        if (err) {
          reject(err);
        } else {
          resolve(this);
        }
      });
    });
  }

  /**
   * Forces Removal of the container.
   *
   * @return {Promise}
   */
  remove() {
    return this._wrap(this.container.remove, {force: true});
  }
}

/**
 * Run solution inside a docker container.
 *
 * Returns a promise resolving to the verification result.
 *
 * @param  {Dockerode} client
 * @param  {Object}    payload
 * @return {Promise}
 */
exports.run = function run(client, payload, logger) {
  if (
    !payload ||
    !payload.language ||
    !images[payload.language]
  ) {
    return Promise.reject(new Error('Unsupported language.'));
  }

  logger = logger || console;

  return new Promise((resolve, reject) => {
    client.createContainer(containerOptions(payload), (err, container) => {
      if (err) {
        reject(err);
      } else {
        resolve(new Verifier(container));
      }
    });
  }).then(
    verifier => verifier.attach()
  ).then(
    verifier => verifier.start()
  ).then(
    verifier => verifier.wait(DELAY)
  ).then(
    verifier => {
      verifier.remove().catch(err => logger.error(err));
      return verifier.out.parse();
    }
  ).catch(err => {
    if (err.verifier) {
      err.verifier.remove().catch(err => logger.error(err));
    }

    return Promise.reject(err);
  });
};

const images = exports.images = {
  /**
   * Pull an image from docker hub.
   *
   * @param  {Docker} client dockerode's Docker instance.
   * @param  {string} image  image name
   * @return {Promise}       Resolve to the pull stream.
   */
  pull: function pullImage(client, image) {
    return new Promise((ok, fails) => {
      client.pull(image, (err, stream) => {
        if (err) {
          fails(err);
        } else {
          ok(stream);
        }
      });
    });
  },

  /**
   * Load list of verifier images availables.
   *
   * @param  {Docker} client dockerode's Docker instance.
   * @return {Promise}       Promise resolving to an image name list
   *                         (the image name with its tag)
   */
  list: function verifierImages(client) {
    return new Promise((ok, fails) => {
      client.listImages({
      }, (err, data) => {
        if (err) {
          fails(err);
        } else {
          ok(
            data.filter(
              i => i.Labels && i.Labels['com.singpath.verifier']
            ).map(
              i => i.RepoTags.filter(t => t.startsWith('singpath/verifier2') && t.endsWith(`:${VERIFIERS_TAG}`))
            ).filter(
              tags => tags.length > 0
            ).map(
              tags => tags[0]
            )
          );
        }
      });
    });
  },

  /**
   * Load list of missing images
   */
  listMissing: function missingVerifierImages(client) {
    images.verifierImages(client).then(images => {
      const found = new Set(images);

      return Object.keys(images).map(
        name => `${images[name]}:${VERIFIERS_TAG}`
      ).filter(
        image => !found.has(image)
      );
    });
  }
};

function containerOptions(payload) {
  return {
    'AttachStdin': false,
    'AttachStdout': true,
    'AttachStderr': true,
    'Tty': false,
    'Cmd': ['verify', JSON.stringify({
      'solution': payload.solution,
      'tests': payload.tests
    })],
    'Image': images[payload.language],
    'HostConfig': {
      'CapDrop': ['All'],
      'NetworkMode': 'none'
    }
  };
}
