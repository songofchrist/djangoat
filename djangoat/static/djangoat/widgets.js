(function($) {

  /* POST PAGE LOAD EXECUTION */
  $(() => {
    /* PrettyJSONTextarea JSON Validator */
    $('.dg-json').keyup(function(e) {
      let $ta = $(this),
        v = $ta.val();
      if (['{', '[', '"'].includes(e.key)) {  // provide help when then characters are entered
        let nc = {'{': ['"":}', 1], '[': [']', 0], '"': ['"', 0]}[e.key],
          ss = $ta[0].selectionStart,
          pt = v.slice(0, ss);
        if (nc[0] !== '"' || pt.charAt(ss - 2) !== '\\') {
          v = pt + nc[0] + v.slice(ss);
          ss += nc[1];
          $ta.val(v);
          $ta[0].setSelectionRange(ss, ss);
        }
      }
      try {
        JSON.parse(v);
        $ta.removeClass('error').data('emsg').hide();
      } catch(emsg) {
        $ta.addClass('error').data('emsg').html(emsg).show();
      }
    }).each(function() {
      let $ta = $(this),
        $emsg = $('<div class="dg-emsg">').hide();
      $ta.wrap('<div>').after($emsg).data('emsg', $emsg);
    });
  });
})(jQuery);