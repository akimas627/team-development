  /* $(document).ready(function () {
    $('#link_music').on('click', function () {
      $(window).scrollTop($('#music').position().top);
    });
});  */


function changeTerm() {
  let id = document.getElementById('genre').value;
  
  if (id=='create-genre') {
    document.getElementById("input-genre").disabled = false;
  } else {
    document.getElementById("input-genre").disabled = true;
  }
}