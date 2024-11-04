document.addEventListener("DOMContentLoaded", function() {
  const form = document.querySelector('form.filtro');
  
  // Manipula cliques nos botões de tipo
  document.addEventListener("click", function(evt) {
    if (evt.target.classList.contains("btn-tipo")) {
      evt.target.classList.toggle("ativo");
      
      // Atualiza inputs hidden dos tipos selecionados
      atualizaTiposSelecionados();
    }
  });

  // Função para atualizar os inputs hidden com tipos selecionados
  function atualizaTiposSelecionados() {
    const tiposAtivos = Array.from(document.querySelectorAll('.btn-tipo.ativo'))
      .map(btn => btn.dataset.type);
    
    // Remove inputs antigos
    const oldInputs = form.querySelectorAll('input[name="tipos"]');
    oldInputs.forEach(input => input.remove());
    
    // Adiciona novos inputs para cada tipo selecionado
    tiposAtivos.forEach(tipo => {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'tipos';
      input.value = tipo;
      form.appendChild(input);
    });
  }

  // Inicializa os inputs hidden com os tipos já selecionados
  atualizaTiposSelecionados();
});
