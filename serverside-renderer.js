"use strict";

var webPage = require('webpage');
var fs = require('fs');
var system = require('system');

var format = "svg";
var scale = 1.0;

// Define the function by ourself since introduced in ECMAScript 6 not yet supported by PhantomJS.
function startsWith(str, start) {
  if (start.length > str.length) {
    return false;
  }
  for (var i = 0; i < start.length; i++) {
    if (str[i] != start[i]) {
      return false;
    }
  }
  return true;
}

for (var i = 1; i < system.args.length; i++) {
  var arg = system.args[i];
  if (arg == "-" || arg == "--help") {
    console.log("Usage:");
    console.log("  serverside-renderer.js [--scale=1.0] [--format=svg] [--help]");
    console.log("");
    console.log("The program reads a WaveDrom description file from stdin and outputs");
    console.log("a grapic in the given format to stdout.");
    console.log("");
    console.log("Arguments:");
    console.log("  --scale=float      Scales the image by the given factor. This only makes sense for PNGs.");
    console.log("                     Default is 1.");
    console.log("  --format=svg       The output format in which to generate the image. Options: svg, png.");
    console.log("                     Default: svg");
    console.log("  --help             Displays this help file.");
    phantom.exit(0);
  } else if (startsWith(arg, "--scale=")) {
    var v = arg.slice("--scale=".length);
    scale = parseFloat(v);
    if (isNaN(scale)) {
      console.log("Invalid float scale: " + v);
      phantom.exit(10);
    }
    if (scale <= 0) {
      console.log("Invalid scale " + scale + ". Scale must be > 0.");
      phantom.exit(10);
    }
  } else if (startsWith(arg, "--format=")) {
    var v = arg.slice("--format=".length).toLowerCase();
    if (format != "svg" && format != "png") {
      console.log("Invalid format: " + v);
      phantom.exit(10);
    }
    format = v;
  } else {
    console.log("Invalid argument: " + arg);
    phantom.exit(10);
  }
}

var content = "<html><head></head><body id='thebody'><script type='WaveDrom'>" +
"{ signal: [" +
"  { name: 'A', wave: '01........0....',  node: '.a........j' }," +
"  { name: 'B', wave: '0.1.......0.1..',  node: '..b.......i' }," +
"  { name: 'C', wave: '0..1....0...1..',  node: '...c....h..' }," +
"  { name: 'D', wave: '0...1..0.....1.',  node: '....d..g...' }," +
"  { name: 'E', wave: '0....10.......1',  node: '.....ef....' }" +
"  ]," +
"  edge: [" +
"    'a~b t1', 'c-~a t2', 'c-~>d time 3', 'd~-e'," +
"    'e~>f', 'f->g', 'g-~>h', 'h~>i some text', 'h~->j'" +
"  ]" +
"}" +
"</script></body></html>";

function renderNewPage(content, size) {
  var page = webPage.create();
  if (typeof size !== "undefined") {
    page.viewportSize = {width: size.width, height: size.height};
  }
  
  page.setContent(content, 'empty');

  var succeeded = page.injectJs("./skins/default.js");
  if (!succeeded) {
    console.log("failed to load ./skins/default.js");
    phantom.exit(1);
  }
  
  var succeeded = page.injectJs("./wavedrom.min.js");
  if (!succeeded) {
    console.log("failed to load wavedrom.js");
    phantom.exit(1);
  }

  page.evaluate(function() {
    WaveDrom.ProcessAll();
  });

  return page;
}

var page = renderNewPage(content);

var node = page.evaluate(function() {
  var body = document.getElementById('thebody');
  
  var div = body.children[0];
  var svg = div.children[0];

  var svgRect = document.querySelector("div > svg").getBoundingClientRect();

  var node = {};
  node.width = svgRect.left + svgRect.right;
  node.height = svgRect.top + svgRect.bottom;
  
  return node;
});

var svgText = page.evaluate(function() {
  var body = document.getElementById('thebody');
  var div = body.children[0];
  return "" + div.innerHTML;
});

console.log("Width:" + node.width);
console.log("Height:" + node.height);

var page = renderNewPage(content, {width: node.width, height: node.height});
page.render("test.png", {format: "png"});

var f = fs.open("test.svg", {mode: 'w', charset: 'UTF-8'});
f.write(svgText);
f.close();

phantom.exit();
