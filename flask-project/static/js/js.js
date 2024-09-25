let buttons = document.querySelectorAll(".btn-tipo");

document.addEventListener("click", function(evt) {

  if (evt.target.classList.contains("btn-tipo")) {

    evt.target.classList.toggle("ativo");
    
  }
});
 const config = {
                    type: 'bar',
                    data: {
                        labels: ['10', '30', '50', '75', '100', '130'],
                        datasets: [{
                            label: '',
                            data: [5, 10, 8, 12, 6, 14], 
                            backgroundColor: 'rgba(128, 128, 128, 0.8)',
                            borderWidth: 1,
                            borderSkipped: false,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    display: true
                                }
                            },
                            y: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    display: false
                                },
                                beginAtZero: true
                            }
                        }
                    }
                };
        
                var ctx1 = document.getElementById('grafico1').getContext('2d');
                var grafico1 = new Chart(ctx1, config);
        
                var ctx2 = document.getElementById('grafico2').getContext('2d');
                var grafico2 = new Chart(ctx2, config);
        
                var ctx3 = document.getElementById('grafico3').getContext('2d');
                var grafico3 = new Chart(ctx3, config);
        
                var ctx4 = document.getElementById('grafico4').getContext('2d');
                var grafico4 = new Chart(ctx4, config);