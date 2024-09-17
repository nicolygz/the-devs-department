let buttons = document.querySelectorAll(".btn-tipo");

document.addEventListener("click", function(evt){

  if(evt.target.classList.contains("btn-tipo")){


    buttons.forEach(function(button){
      button.classList.remove("ativo");
    });

    evt.target.classList.add("ativo");
    
  }
});