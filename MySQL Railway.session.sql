SELECT * from proposicoes;
SELECT * FROM vereadores;


DESCRIBE proposicoes;

SELECT v.ver_nome, COUNT(p.id_prop) AS qtd_proposicoes
FROM vereadores v
LEFT JOIN proposicoes p ON v.ver_id = p.ver_id
GROUP BY v.ver_id
ORDER BY qtd_proposicoes DESC;

