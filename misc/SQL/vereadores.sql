create database vereadoresDB;
use vereadoresDB;

DROP TABLE IF EXISTS vereadores;
create table vereadores (
	ver_id mediumint primary key,
    ver_nome varchar(50) not null,
    ver_partido varchar(50) not null,
    ver_tel1 varchar(20),
    ver_tel2 varchar(20),
    ver_celular varchar(50),
    ver_email varchar(40) not null,
    ver_gabinete varchar(25),
    ver_posicionamento varchar(255),
    ver_foto varchar(255)
);

create table assiduidade (
	ano smallint not null,
    presenca smallint not null,
    faltas smallint not null,
    justif smallint not null,
    ver_id mediumint not null,
    foreign key (ver_id) references vereadores(ver_id)
);


DROP TABLE if exists comissoes;
create table comissoes (
	id tinyint primary key not null,
	nome varchar(255) not null,
    tema varchar(40) not null,
    data_inicio date not null,
    data_fim date not null,
    link text not null
);

create table vereadores_comissoes (
	id smallint primary key auto_increment,
    ver_id mediumint not null,
    comissao_id tinyint not null,
    cargo varchar(255) not null,
    foreign key(ver_id) references vereadores(ver_id),
    foreign key(comissao_id) references comissoes(id)
);

CREATE TABLE avaliacao (
    id SMALLINT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50) NOT NULL,
    nota TINYINT NOT NULL CHECK (nota BETWEEN 0 AND 5),  -- Restringe 'nota' entre 0 e 5
    comentario TEXT NOT NULL CHECK (CHAR_LENGTH(comentario) >= 20),  -- Exige que 'comentario' tenha pelo menos 20 caracteres
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Define a data e hora da criação da avaliação
    ver_id mediumint NOT NULL,
    FOREIGN KEY (ver_id) REFERENCES vereadores(ver_id)
);

create table votacao (
	id smallint primary key auto_increment,
    num_pl MEDIUMINT not null,
    ano_pl smallint not null,
    resultado varchar(50) not null,
    presidente mediumint not null,
    autoria_pl mediumint not null,
    foreign key (presidente) references vereadores (ver_id),
    foreign key (autoria_pl) references vereadores(ver_id),
    UNIQUE (num_pl, ano_pl)
);

create table extrato_votacao (
	votacao_id smallint not null,
    ver_id mediumint not null,
    voto varchar(15) not null,
    foreign key (votacao_id) references votacao(id),
    foreign key (ver_id) references vereadores(ver_id)
);

-- data_hora	situacao	id_vereador	tipo	tema

create table proposicoes (
	requerimento_num varchar(30) not null,
    ementa text not null,
    num_processo varchar(30) not null,
    num_protocolo mediumint not null,
    id_prop mediumint not null unique,
    data_hora datetime not null,
    situacao varchar(20) not null,
    tipo varchar(20) not null, -- mocoes ou pl ou requerimento
	ver_id mediumint not null,
    tema varchar(255) not null,
    foreign key(ver_id) references vereadores(ver_id)
);

SHOW TABLES;