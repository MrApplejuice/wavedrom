"use strict";

var webPage = require('webpage');
var fs = require('fs');
var system = require('system');

var outputFile = null;
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

var parseMoreArgs = true;
for (var i = 1; i < system.args.length; i++) {
  var arg = system.args[i];
  
  if (!parseMoreArgs || !startsWith(arg, "-")) {
    if (outputFile !== null) {
      console.log("Only a single output filename is allowed");
      phantom.exit(10);
    }
    
    outputFile = arg;
  } else if (arg == "--") {
    parseMoreArgs = false;
  } else if (arg == "-" || arg == "--help") {
    console.log("Usage:");
    console.log("  serverside-renderer.js [--scale=1.0] [--format=svg] [--help] filename");
    console.log("");
    console.log("The program reads a WaveDrom description file from stdin and outputs");
    console.log("a graphic in the given format to stdout.");
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
if (outputFile === null) {
  console.log("Output filename expected!");
  phantom.exit(10);
  console.log("this is needed somehow, otherwise phantomjs does not quit?!");
}

var graphStr = "";
while (!system.stdin.atEnd()) {
  graphStr = graphStr + system.stdin.read(1024);
}

var content = "<html><head></head><body id='thebody'><script type='WaveDrom'>" + graphStr + "</script></body></html>";

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

if (format == "svg") {
  var svgText = page.evaluate(function() {
    var body = document.getElementById('thebody');
    var div = body.children[0];
    return "" + div.innerHTML;
  });

  var f = fs.open(outputFile, {mode: 'w', charset: 'UTF-8'});
  f.write(svgText);
  f.close();
} else {
  var page = renderNewPage(content, {width: Math.round(node.width * scale), height: Math.round(node.height * scale)});
  page.render(outputFile, {format: "png"});
}

phantom.exit();
