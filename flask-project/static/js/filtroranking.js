document.getElementById('filtro').addEventListener('change', function() {
    const criterio = this.value;
    if (criterio === 'default') return;

    console.log('Critério selecionado:', criterio);

    fetch(`/filtrar/${criterio}`)
        .then(response => response.json())
        .then(data => {
            console.log('Dados recebidos:', data);
        })
        .catch(error => {
            console.error('Erro ao buscar dados:', error);
        });
});

function atualizarRanking(data, criterio) {
    console.log('Atualizando ranking com critério:', criterio);
    const container = document.querySelector('.ranking-container');
    container.innerHTML = '';

    data.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = 'vereador-card';
        
        let metrica = '';
        switch(criterio) {
            case 'proposicoes':
                metrica = `${item.qtd} proposições`;
                break;
            case 'assiduidade':
                metrica = `${item.presencas} presenças`;
                break;
            case 'comissoes':
                metrica = `${item.participacoes} comissões`;
                break;
            case 'avaliacoes':
                metrica = `Nota: ${item.media.toFixed(1)}`;
                break;
        }

        console.log(`Criando card para ${item.nome} com métrica: ${metrica}`);
        
        card.innerHTML = `
            <h3>${index + 1}º - ${item.nome}</h3>
            <p>${metrica}</p>
        `;
        
        container.appendChild(card);
    });
}
