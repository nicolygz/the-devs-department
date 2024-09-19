function showContent(contentType) {
    // Esconde todos os conteúdos com animação
    var resumo = document.getElementById('resumo');
    var proposicoes = document.getElementById('proposicoes');

    resumo.classList.remove('show');
    proposicoes.classList.remove('show');

    // Aguarda a animação de "fade out" antes de esconder completamente
    setTimeout(function() {
        resumo.style.display = 'none';
        proposicoes.style.display = 'none';
        
        // Mostra o conteúdo com animação "fade in"
        var selectedContent = document.getElementById(contentType);
        selectedContent.style.display = 'block';
        setTimeout(function() {
            selectedContent.classList.add('show');
        }, 10); // Leve delay para garantir o efeito
    }, 500); // Tempo igual ao `transition` do CSS (0.5s)
}

// Mostra o Resumo Político inicialmente
document.getElementById('resumo').classList.add('show');
document.getElementById('resumo').style.display = 'block';

const stars = document.querySelectorAll('.stars input');

