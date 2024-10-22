function showContent(contentType) {
    // Esconde todos os conteúdos com animação
    var resumo = document.getElementById('resumo');
    var proposicoes = document.getElementById('proposicoes');

    resumo.classList.remove('show');
    proposicoes.classList.remove('show');

    // Aguarda a animação de "fade out" antes de esconder completamente
    setTimeout(function () {
        resumo.style.display = 'none';
        proposicoes.style.display = 'none';

        // Mostra o conteúdo com animação "fade in"
        var selectedContent = document.getElementById(contentType);
        selectedContent.style.display = 'block';
        setTimeout(function () {
            selectedContent.classList.add('show');
        }, 10); // Leve delay para garantir o efeito
    }, 500); // Tempo igual ao `transition` do CSS (0.5s)
}

// Mostra o Resumo Político inicialmente
document.getElementById('resumo').classList.add('show');
document.getElementById('resumo').style.display = 'block';

const stars = document.querySelectorAll('.stars input');

// Atualização do Botão
let isUpdating = false; // Variável para controlar o estado de atualização

function updateData(event) {
    event.preventDefault(); // Previne o comportamento padrão do link

    if (isUpdating) return; // Se já estiver atualizando, não faz nada

    isUpdating = true; // Indica que a atualização está em andamento
    const btnContainer = document.getElementById("btnContainer");

    // Muda a cor de fundo do contêiner do botão
    btnContainer.style.backgroundColor = "#ffa100";

    // Faz a requisição para o servidor
    fetch(document.getElementById("updateButton").href)
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Erro na requisição');
            }
        })
        .then(data => {
            console.log(data);
        })
        .catch(error => {
            console.error('Erro:', error);
        })
        .finally(() => {
            // Restaura a cor original após a requisição
            btnContainer.style.backgroundColor = "";

            // Espera 30 segundos antes de permitir outra atualização
            setTimeout(() => {
                isUpdating = false; // Permite nova atualização
            }, 30000);
        });
}



