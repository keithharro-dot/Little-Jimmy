// Test stand-in for qrcodejs: writes the QR's text into the element so tests can read the join link.
window.QRCode=function(el,o){el.textContent='QR:'+o.text};QRCode.CorrectLevel={M:0};
