$(function() {
  $('button#submitButton').on('click', function() {
    var $btn = $(this).button('loading');
    $.ajax({
             type: 'POST',
             url: 'search',
             data: $('form').serialize(),
             success: function(msg) {
               $('#searchResults').replaceWith(msg);
               $btn.button('reset');
             },
             error: function() {
               $('#searchResults').html('A server error has occurred');
               $btn.button('reset');
             }
           });
  });

  $('button#addPhase').click(function() {
    var numRows = $('table#flightPhases tr').length;
    var id = 'flightPhases' + numRows;
    $('table#flightPhases tr:last').after(
        '<tr id="' + id + '">' +
        '<td><input type="number" name="delta-v" step="0.1" value="0"/></td>' +
        '<td><input type="number" name="acceleration" step="0.01" value="0"/></td>' +
        '<td><input type="number" name="pressure" value="0"/></td>' +
        '</tr>'
    );
  });

  $('button#addTransferStages').on('click', function() {
    var $btn = $(this).button('loading');
    $.ajax({
      type: 'POST',
      url: 'transferstages',
      data: $('form').serialize(),
      success: function(msg) {
        alert("Add transfer stages! " + msg)
        $('#searchResults').replaceWith(msg);
        $btn.button('reset');
      },
      error: function() {
        $('#searchResults').html('A server error has occurred');
        $btn.button('reset');
      }
    });
  });

  $('button#removePhase').click(function() {
    // The last two rows (header and single phase) may never be deleted.
    var numRows = $('table#flightPhases tr').length;
    if (numRows <= 2) {
      return
    }
    $('table#flightPhases tr:last').remove();
  });

  $('input#payload').on('click', selectSelf);
  $('table#flightPhases').on('click', 'input[type="number"]', selectSelf);
});

function selectSelf() {
  $(this).select();
}
