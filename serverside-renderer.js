var webPage = require('webpage');

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

console.log(node.width);
console.log(node.height);

var page = renderNewPage(content, {width: node.width, height: node.height});
page.render("test.png", {format: "png"});
phantom.exit();
