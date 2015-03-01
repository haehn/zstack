var D = D || {};

D.controller = function(viewer) {

  this._viewer = viewer;

  this._uids = {};

};


D.controller.prototype.receive = function(message) {

  var data = message.data;

  if (bytes2str(data.slice(0,7), 7) == "welcome") {

    this._viewer.initialize();

  } else if (bytes2str(data.slice(0,4), 4) == "wait") {

    var uid = bytes2str(data.slice(5));
    this._uids[uid] = false;
    console.log('Waiting for', uid);

  } else if (bytes2str(data.slice(0,4), 4) == "done") {

    var uid = bytes2str(data.slice(5));
    this._uids[uid] = true;
    console.log('Ready to load', uid)

    this.load_data(uid);
    
  } else {

    console.log('Got image data', data.byteLength)

    var convertedData = bytes2str(data);
    var encodedData = window.btoa(convertedData);

    var image = new Image();
    image.src = 'data:image/jpeg;base64,'+encodedData;
    image.onload = function() {

      this._viewer.draw(image);

    }.bind(this);

  }

};


D.controller.prototype.request_data = function(z, roi, zoomlevel) {

  var out = {};
  out.name = 'PREPARE';
  out.value = [z, roi, zoomlevel];
  this._viewer._websocket.send(JSON.stringify(out))

};

D.controller.prototype.load_data = function(uid) {

  var out = {};
  out.name = 'GET';
  out.value = [uid];
  this._viewer._websocket.send(JSON.stringify(out))

};