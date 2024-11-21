document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector('form.filtro');
    const tiposButtons = document.querySelectorAll('.btn-tipo');
    
    function atualizaTiposSelecionados() {
        form.querySelectorAll('input[name="tipos"]').forEach(input => input.remove());
        
        document.querySelectorAll('.btn-tipo.ativo').forEach(btn => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'tipos';
            input.value = btn.getAttribute('data-tipo');
            form.appendChild(input);
        });
    }

    // Adiciona evento de clique aos botões de tipo
    tiposButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            this.classList.toggle('ativo');
            atualizaTiposSelecionados();
            // Remove submissão automática do formulário
        });
    });

    // Inicializa os inputs hidden com os tipos já selecionados
    atualizaTiposSelecionados();
});
