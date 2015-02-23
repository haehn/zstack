

function nearestPOT(value) {

  var v = value;
  v |= v >> 1;
  v |= v >> 2;
  v |= v >> 4;
  v |= v >> 8;
  v |= v >> 16;
  v = v - (v >> 1);

  var w = value;
  w--;
  w |= w >> 1;
  w |= w >> 2;
  w |= w >> 4;
  w |= w >> 8;
  w |= w >> 16;
  w++;

  var v_distance = Math.abs(value - v);
  var w_distance = Math.abs(value - w);

  if (v_distance <= w_distance) {
    return v;
  } else {
    return w;
  }
}

//
// shader utility functions
//
function readAndCompileShader(gl, id) {

  var shaderScript = document.getElementById(id);

  if (!shaderScript) {
    return null;
  }

  var str = "";
  var k = shaderScript.firstChild;
  while (k) {
    if (k.nodeType == 3) {
      str += k.textContent;
    }
    k = k.nextSibling;
  }

  var shader;
  if (shaderScript.type == "x-shader/x-fragment") {
    shader = gl.createShader(gl.FRAGMENT_SHADER);
  } else if (shaderScript.type == "x-shader/x-vertex") {
    shader = gl.createShader(gl.VERTEX_SHADER);
  } else {
    return null;
  }
  
  gl.shaderSource(shader, str);
  gl.compileShader(shader);

  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.log(gl.getShaderInfoLog(shader));
    return null;
  }

  return shader;

};

function linkShaders(gl, vs_id, fs_id) {

  var fragmentShader = readAndCompileShader(gl, fs_id);
  var vertexShader = readAndCompileShader(gl, vs_id);

  var shaderProgram = gl.createProgram();
  gl.attachShader(shaderProgram, vertexShader);
  gl.attachShader(shaderProgram, fragmentShader);
  gl.linkProgram(shaderProgram);

  if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
      console.log("Could not initialise shaders");

      console.log(gl.getShaderInfoLog(fragmentShader));
      console.log(gl.getShaderInfoLog(vertexShader));
      console.log(gl.getProgramInfoLog(shaderProgram));

      return null;

  }

  return shaderProgram;

};
