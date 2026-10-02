DROP TABLE IF EXISTS servicos_solicitacoes;
DROP TABLE IF EXISTS auditoria_logs;
DROP TABLE IF EXISTS notificacoes;
DROP TABLE IF EXISTS penalidades;
DROP TABLE IF EXISTS renovacoes;
DROP TABLE IF EXISTS reservas;
DROP TABLE IF EXISTS sessoes;
DROP TABLE IF EXISTS emprestimos;
DROP TABLE IF EXISTS livros;
DROP TABLE IF EXISTS usuarios;






CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    endereco VARCHAR(255),
    prontuario VARCHAR(30) UNIQUE,
    curso VARCHAR(150),
    ano_ingresso INTEGER,
    tipo_usuario VARCHAR(50) NOT NULL DEFAULT 'Discente Regular',
    perfil VARCHAR(30) NOT NULL DEFAULT 'Usuário',
    senha VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'Ativo',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cpf TEXT UNIQUE,
    data_nascimento TEXT,
    matricula TEXT UNIQUE
);




CREATE TABLE livros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo VARCHAR(250) NOT NULL,
    subtitulo VARCHAR(250),
    autor VARCHAR(200) NOT NULL,
    editora VARCHAR(200),
    local_publicacao VARCHAR(120),
    ano INTEGER,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    assuntos TEXT,
    palavras_chave TEXT,
    numero_paginas INTEGER,
    serie VARCHAR(150),
    colecao VARCHAR(150),
    volume VARCHAR(30),
    resumo TEXT,
    imagem_capa VARCHAR(500),
    categoria VARCHAR(100),
    localizacao VARCHAR(60),
    quantidade INTEGER NOT NULL DEFAULT 1,
    disponivel INTEGER NOT NULL DEFAULT 1
);




CREATE TABLE emprestimos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    livro_id INTEGER NOT NULL,
    data_emprestimo DATE NOT NULL DEFAULT CURRENT_DATE,
    data_prevista_devolucao DATE NOT NULL,
    data_devolucao DATE,
    renovacoes INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'Emprestado',
    CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_livro FOREIGN KEY (livro_id) REFERENCES livros(id) ON DELETE CASCADE
);





CREATE TABLE renovacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emprestimo_id INTEGER NOT NULL,
    data_renovacao DATE NOT NULL DEFAULT CURRENT_DATE,
    nova_data_prevista DATE NOT NULL,
    CONSTRAINT fk_emprestimo FOREIGN KEY (emprestimo_id) REFERENCES emprestimos(id) ON DELETE CASCADE
);





CREATE TABLE reservas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    livro_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    data_reserva TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'Ativa',
    notificado INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_livro FOREIGN KEY (livro_id) REFERENCES livros(id) ON DELETE CASCADE,
    CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);





CREATE TABLE penalidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    emprestimo_id INTEGER,
    dias_atraso INTEGER NOT NULL DEFAULT 0,
    dias_suspensao INTEGER NOT NULL DEFAULT 0,
    data_inicio DATE NOT NULL DEFAULT CURRENT_DATE,
    data_fim DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Ativa',
    descricao VARCHAR(255),
    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_emprestimo FOREIGN KEY (emprestimo_id) REFERENCES emprestimos(id) ON DELETE SET NULL
);




CREATE TABLE notificacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    tipo VARCHAR(50),
    mensagem TEXT,
    lida INTEGER NOT NULL DEFAULT 0,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);




CREATE TABLE auditoria_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_responsavel VARCHAR(150),
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operacao VARCHAR(100) NOT NULL,
    dados_afetados TEXT
);




CREATE TABLE servicos_solicitacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    descricao TEXT,
    dados_json TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'Pendente',
    data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_resposta TIMESTAMP,
    resposta TEXT,
    CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);




CREATE TABLE sessoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token VARCHAR(64) UNIQUE NOT NULL,
    usuario_id INTEGER NOT NULL,
    criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);




CREATE INDEX idx_emprestimos_usuario ON emprestimos (usuario_id);
CREATE INDEX idx_emprestimos_livro ON emprestimos (livro_id);
CREATE INDEX idx_emprestimos_status ON emprestimos (status);
CREATE INDEX idx_reservas_livro ON reservas (livro_id);
CREATE INDEX idx_reservas_usuario ON reservas (usuario_id);
CREATE INDEX idx_notificacoes_usuario ON notificacoes (usuario_id);
CREATE INDEX idx_penalidades_usuario ON penalidades (usuario_id);
CREATE INDEX idx_auditoria_data ON auditoria_logs (data_hora);
CREATE INDEX idx_livros_titulo ON livros (titulo);
CREATE INDEX idx_livros_autor ON livros (autor);





INSERT OR IGNORE INTO usuarios (nome, email, telefone, endereco, prontuario, curso, ano_ingresso, tipo_usuario, perfil, status) VALUES
    ('Ana Beatriz Silva',      'ana.silva@email.com',       '(11) 99999-0001', 'Rua das Flores, 100 - Capivari', 'CV2023001', 'Informática',        2023, 'Discente Regular', 'Usuário',       'Ativo'),
    ('Carlos Eduardo Santos',  'carlos.santos@email.com',   '(11) 99999-0002', 'Av. da Indústria, 200 - Capivari', NULL, NULL, 2019, 'Servidor', 'Bibliotecário', 'Ativo'),
    ('Mariana Oliveira Costa', 'mariana.costa@email.com',   '(11) 99999-0003', 'Rua dos Pinheiros, 50 - Capivari', 'CV2022001', 'Eletrônica',        2022, 'Discente Regular', 'Usuário',       'Ativo'),
    ('Pedro Henrique Lima',    'pedro.lima@email.com',      '(11) 99999-0004', 'Rua do Comércio, 300 - Capivari', 'CV2021010', 'Mecânica',          2021, 'Discente FIC',     'Usuário',       'Ativo'),
    ('Juliana Ferreira Martins','juliana.martins@email.com','(11) 99999-0005', 'Rod. SP-101, km 5 - Capivari',    NULL, NULL, 2020, 'Terceirizado',      'Usuário',       'Ativo'),
    ('Rafael Souza Almeida',   'rafael.almeida@email.com',  '(11) 99999-0006', 'Rua da Estação, 45 - Capivari',   'CV2020007', 'Administração',     2020, 'Discente Regular', 'Usuário',       'Suspenso')
;

INSERT OR IGNORE INTO livros (titulo, subtitulo, autor, editora, local_publicacao, ano, isbn, assuntos, palavras_chave, numero_paginas, serie, colecao, volume, resumo, categoria, localizacao, quantidade, disponivel) VALUES
    ('Dom Casmurro', 'Romance', 'Machado de Assis', 'Garnier', 'Rio de Janeiro', 1899, '978-85-01-00001-1', 'Literatura Brasileira; Romances', 'machado; ciúme; bentinho', 256, NULL, 'Clássicos da Literatura', 'Vol. 1', 'O clássico da dúvida de Bentinho em relação a Capitu.', 'Literatura Brasileira', 'A-01', 5, 5),
    ('O Senhor dos Anéis', 'A Sociedade do Anel', 'J.R.R. Tolkien', 'HarperCollins', 'São Paulo', 1954, '978-85-01-00002-8', 'Fantasia', 'anel; tolkien; terra média', 576, NULL, 'O Senhor dos Anéis', 'Vol. 1', 'A jornada de Frodo para destruir o anel do poder.', 'Fantasia', 'B-02', 3, 3),
    ('1984', 'Romance distópico', 'George Orwell', 'Companhia das Letras', 'São Paulo', 1949, '978-85-01-00003-5', 'Ficção Científica; Distopia', 'orwell; big brother; ditadura', 336, NULL, 'Clássicos', 'Vol. 1', 'Uma sociedade sob vigilância totalitária.', 'Ficção Científica', 'C-03', 4, 4),
    ('Orgulho e Preconceito', 'Romance de época', 'Jane Austen', 'Penguin', 'Rio de Janeiro', 1813, '978-85-01-00004-2', 'Romance', 'austen; elizabeth; darcy', 424, NULL, 'Clássicos', 'Vol. 1', 'As desventuras amorosas de Elizabeth Bennet.', 'Romance', 'D-04', 2, 2),
    ('O Pequeno Príncipe', 'Com aquarelas do autor', 'Antoine de Saint-Exupéry', 'Agir', 'Rio de Janeiro', 1943, '978-85-01-00005-9', 'Infantil; Filosofia', 'príncipe; rosa; raposa', 96, NULL, NULL, NULL, 'A essência das coisas é invisível aos olhos.', 'Infantil', 'E-05', 6, 6),
    ('Grande Sertão: Veredas', 'Romance', 'Guimarães Rosa', 'Companhia das Letras', 'São Paulo', 1956, '978-85-01-00006-6', 'Literatura Brasileira', 'riobaldo; sertão; jagunço', 608, NULL, NULL, NULL, 'A saga de Riobaldo pelo sertão mineiro.', 'Literatura Brasileira', 'A-06', 2, 2),
    ('A Guerra dos Tronos', 'As Crônicas de Gelo e Fogo', 'George R.R. Martin', 'Suma', 'Rio de Janeiro', 1996, '978-85-01-00007-3', 'Fantasia', 'westeros; stark; lannister', 700, 'As Crônicas de Gelo e Fogo', NULL, 'Livro 1', 'A disputa pelo trono de ferro em Westeros.', 'Fantasia', 'B-07', 3, 3),
    ('O Código Da Vinci', 'Thriller', 'Dan Brown', 'Sextante', 'Rio de Janeiro', 2003, '978-85-01-00008-0', 'Suspense', 'robert langdon; código; mistério', 448, NULL, NULL, NULL, 'Um assassinato no Louvre desencadeia um mistério.', 'Suspense', 'F-08', 4, 4),
    ('A Revolução dos Bichos', 'Fábula política', 'George Orwell', 'Companhia das Letras', 'São Paulo', 1945, '978-85-01-00009-7', 'Ficção Científica; Política', 'orwell; fazenda; revolução', 152, NULL, 'Clássicos', 'Vol. 1', 'Os animais tomam o poder da fazenda.', 'Ficção Científica', 'C-09', 3, 3),
    ('Memórias Póstumas de Brás Cubas', 'Romance', 'Machado de Assis', 'Penguin', 'Rio de Janeiro', 1881, '978-85-01-00010-3', 'Literatura Brasileira', 'machado; memórias; cubas', 240, NULL, 'Clássicos da Literatura', 'Vol. 1', 'O defunto autor narra suas memórias.', 'Literatura Brasileira', 'A-10', 2, 2)
;


INSERT INTO emprestimos (usuario_id, livro_id, data_emprestimo, data_prevista_devolucao, data_devolucao, renovacoes, status) VALUES
    (1, 1, date('now','-8 days'),  date('now','-1 day'),  NULL, 0, 'Emprestado'),
    (2, 3, date('now','-5 days'),  date('now','+2 days'), NULL, 0, 'Emprestado'),
    (3, 5, date('now','-12 days'), date('now','+9 days'), NULL, 1, 'Emprestado'),
    (4, 6, date('now','-10 days'), date('now','-3 days'), NULL, 0, 'Emprestado'),
    (5, 2, date('now','-3 days'),  date('now','+4 days'), NULL, 0, 'Emprestado'),
    (1, 7, date('now','-20 days'), date('now','-6 days'), date('now','-10 days'), 0, 'Devolvido'),
    (2, 8, date('now','-30 days'), date('now','-16 days'), date('now','-20 days'), 1, 'Devolvido'),
    (3, 4, date('now','-15 days'), date('now','-1 day'),  date('now','-2 days'), 0, 'Devolvido');

INSERT INTO renovacoes (emprestimo_id, data_renovacao, nova_data_prevista) VALUES
    (3, date('now','-5 days'), date('now','+9 days')),
    (7, date('now','-18 days'), date('now','-16 days'));

INSERT INTO reservas (livro_id, usuario_id, data_reserva, status, notificado) VALUES
    (1, 2, date('now','-3 days'), 'Ativa', 0),
    (1, 3, date('now','-2 days'), 'Ativa', 0),
    (6, 1, date('now','-1 day'),  'Ativa', 0),
    (10, 5, date('now','-4 days'), 'Cancelada', 0);

INSERT INTO penalidades (usuario_id, emprestimo_id, dias_atraso, dias_suspensao, data_inicio, data_fim, status, descricao) VALUES
    (4, 4, 3, 6,  date('now','-3 days'),  date('now','+3 days'), 'Ativa', 'Atraso de 3 dias na devolução de Grande Sertão: Veredas'),
    (6, NULL, 10, 20, date('now','-5 days'), date('now','+15 days'), 'Ativa', 'Atraso de 10 dias na devolução de material');

INSERT INTO notificacoes (usuario_id, tipo, mensagem, lida, data_criacao) VALUES
    (1, 'prazo_proximo', 'O prazo de devolução de Dom Casmurro vence em breve.', 0, date('now','-1 day')),
    (2, 'emprestimo', 'Empréstimo de 1984 realizado com sucesso.', 1, date('now','-5 days')),
    (4, 'atraso', 'Seu empréstimo de Grande Sertão: Veredas está em atraso.', 0, date('now','-3 days')),
    (6, 'suspensao', 'Você foi suspenso por atraso de 10 dias. Suspensão de 20 dias aplicada.', 0, date('now','-5 days'));

INSERT INTO auditoria_logs (usuario_responsavel, data_hora, operacao, dados_afetados) VALUES
    ('Administrador', date('now','-2 days'), 'Cadastro de Livro', '{"titulo": "Dom Casmurro"}'),
    ('Administrador', date('now','-2 days'), 'Cadastro de Usuário', '{"nome": "Ana Beatriz Silva"}'),
    ('Carlos Eduardo Santos', date('now','-8 days'), 'Empréstimo realizado', '{"usuario": "Ana Beatriz Silva", "livro": "Dom Casmurro"}');

INSERT INTO servicos_solicitacoes (usuario_id, tipo, descricao, dados_json, status, data_solicitacao) VALUES
    (1, 'Declaração de Nada Consta', 'Declaração para renovação de bolsa', '{"motivo": "Renovação de bolsa"}', 'Pendente', date('now','-1 day')),
    (3, 'Sugestão de Aquisição', 'Livro de Inteligência Artificial para o curso de Informática', '{"titulo": "Inteligência Artificial: Uma Abordagem Moderna"}', 'Em Análise', date('now','-4 days')),
    (5, 'Ficha Catalográfica', 'Necessário para dissertação', '{"curso": "Mestrado"}', 'Concluída', date('now','-10 days'));
