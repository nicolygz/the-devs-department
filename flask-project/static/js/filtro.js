let buttons = document.querySelectorAll(".btn-tipo");

document.addEventListener("click", function(evt) {

  if (evt.target.classList.contains("btn-tipo")) {

    evt.target.classList.toggle("ativo");
    
  }
});
