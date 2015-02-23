var D = D || {};

D.offscreen_renderer = function(canvas) {

  this._gl = null;

  this._program = null;

  this._canvas = canvas;

  this._width = this._canvas.width;
  this._height = this._canvas.height;

};

D.offscreen_renderer.prototype.init = function(vs_id, fs_id) {

  var canvas = this._canvas;
  var gl = canvas.getContext('experimental-webgl') || canvas.getContext('webgl');

  if (!gl) {
    return false;
  }

  gl.viewport(0, 0, this._width, this._height);
  gl.clearColor(0,0,0,1.);//128./255., 200./255., 255./255., 1.);
  gl.clearDepth(0);

  // enable transparency
  gl.blendEquation(gl.FUNC_ADD);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  gl.enable(gl.BLEND);


  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);

  // create shaders
  this._program = linkShaders(gl, vs_id, fs_id);
  var h = this._program;
  if (!h) {
    return false;
  }
  gl.useProgram(h);

  // textures
  this.h_uImageSampler = gl.getUniformLocation(h, 'uImageSampler');

  this.h_aPosition = gl.getAttribLocation(h, 'aPosition');
  this.h_aTexturePosition = gl.getAttribLocation(h, 'aTexturePosition');

  // create geometry
  this._square_buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, this._square_buffer);
  var vertices = new Float32Array([
    -1, -1., 0.,
     1., -1., 0.,
    -1.,  1., 0.,
    1.,  1., 0.
    ]);
  gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

  this._gl = gl;

  this.init_buffers();

  return true;

};

D.offscreen_renderer.prototype.init_buffers = function() {

  var gl = this._gl;

  // create image texture buffer
  this._image_texture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, this._image_texture);

  // clamp to edge
  

  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);

  gl.bindTexture(gl.TEXTURE_2D, null);  


  // u-v
  this._uv_buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, this._uv_buffer);
  var uvs = new Float32Array([
    0., 0.,
    1., 0.,
    0., 1.,
    1., 1.
    ]);
  gl.bufferData(gl.ARRAY_BUFFER, uvs, gl.STATIC_DRAW);  

};

D.offscreen_renderer.prototype.draw = function(i, width, height) {

  var gl = this._gl;

  gl.viewport(0, 0, this._width, this._height);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);


  // create image texture buffer
  gl.bindTexture(gl.TEXTURE_2D, this._image_texture);
  // gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, gl.LUMINANCE, gl.UNSIGNED_BYTE, i);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, width, height, 0, gl.LUMINANCE, gl.UNSIGNED_BYTE,i )



  // now really draw
  gl.enableVertexAttribArray(this.h_aPosition);
  gl.bindBuffer(gl.ARRAY_BUFFER, this._square_buffer);
  gl.vertexAttribPointer(this.h_aPosition, 3, gl.FLOAT, false, 0, 0);


  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, this._image_texture);
  gl.uniform1i(this.h_uTextureSampler, 0);

  gl.enableVertexAttribArray(this.h_aTexturePosition);
  gl.bindBuffer(gl.ARRAY_BUFFER, this._uv_buffer);
  gl.vertexAttribPointer(this.h_aTexturePosition, 2, gl.FLOAT, false, 0, 0);  

  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

  // var array = new Uint8Array(1048576);
  // gl.readPixels(0, 0, 512, 512, gl.RGBA, gl.UNSIGNED_BYTE, array);
  // console.log(array);

  // c.drawImage(this._canvas,0,0);

};