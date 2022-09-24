/* $(document).ready(function () {
    $('#link_hobby').on('click', function () {
      $(window).scrollTop($('#hobby').position().top);
    });
}); */

function changeTerm() {
  let id = document.getElementById('genre').value;
  
  if (id=='create-genre') {
    document.getElementById("input-genre").disabled = false;
  } else {
    document.getElementById("input-genre").disabled = true;
  }
}