var D = D || {};

D.viewer = function(container) {

  var canvas = document.createElement('canvas');
  canvas.width = container.clientWidth;
  canvas.height = container.clientHeight;
  container.appendChild(canvas);


  this._canvas = canvas;
  this._context = canvas.getContext('2d');
  this._camera = new D.camera(this);
  this._interactor = new D.interactor(this);

  this._controller = new D.controller(this);
  this._websocket = new D.websocket(this);  

  this.render()

};

D.viewer.prototype.initialize = function() {
  this.show(0,0,0);
};

D.viewer.prototype.show = function(z, i, zoomlevel) {

  var width = this._canvas.width;
  var height = this._canvas.height;

  var offset_x = i*width;
  var offset_y = i*height;
  console.time("a")
  this._controller.request_data(z, [offset_x,offset_x+height,offset_y,offset_y+width], zoomlevel)

};

D.viewer.prototype.clear = function() {
  this._context.clearRect(0, 0, this._canvas.width, this._canvas.height);
};

D.viewer.prototype.draw = function(image) {

  this._context.drawImage(image, 0, 0);

};

D.viewer.prototype.render = function() {

  this._context.setTransform(this._camera._view[0], this._camera._view[1], this._camera._view[3], this._camera._view[4], this._camera._view[6], this._camera._view[7]);



  this._AnimationFrameID = window.requestAnimationFrame(this.render.bind(this));

};


D.viewer.prototype.xy2uv = function(x, y) {

  var u = x - this._camera._view[6];
  var v = y - this._camera._view[7];

  return [u, v];

};


D.viewer.prototype.uv2xy = function(u, v) {

  return [u + this._camera._view[6], v + this._camera._view[7]];

};

// returns the pixel coordinates looking at the largest image
D.viewer.prototype.xy2ij = function(x, y) {

  var u_v = this.xy2uv(x, y);

  if (u_v[0] == -1 || u_v[1] == -1) {
    return [-1, -1];
  }

  // var i_j = [Math.floor(((u_v[0]/this._image.zoom_levels[this._camera._w][2])*this._image.zoom_levels[0][2])/this._camera._view[0]), 
  //            Math.floor(((u_v[1]/this._image.zoom_levels[this._camera._w][3])*this._image.zoom_levels[0][3])/this._camera._view[4])];

  var i_j = [0,0]

  return i_j;

};