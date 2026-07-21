(function($) {

  /* POST PAGE LOAD EXECUTION */
  $(() => {
    /* PrettyJSONTextarea JSON Validator */
    $('.dg-json').keyup(function() {
      let $ta = $(this);
      try {
        JSON.parse($ta.val());
        $ta.removeClass('error').data('emsg').hide();
      } catch(e) {
        $ta.addClass('error').data('emsg').html(e).show();
      }
    }).each(function() {
      let $ta = $(this),
        $emsg = $('<div class="dg-json-emsg">').hide();
      $ta.wrap('<div>').after($emsg).data('emsg', $emsg);
    });
  });
})(jQuery);