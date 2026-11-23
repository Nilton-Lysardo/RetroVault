# 🕹️ RetroVault - Gerenciador de ROMs e Jogos Retrô

O **RetroVault** é uma interface web moderna e intuitiva para organizar, explorar e iniciar sua coleção de jogos retrô diretamente pelo navegador.

---

## ✨ Funcionalidades

- **Biblioteca Unificada:** Suporte para múltiplos consoles clássicos (SNES, NES, Mega Drive, Master System, PS1, Nintendo DS, GBA, MAME, Neo Geo, etc.).
- **Lançamento Direto:** Inicie os jogos com um clique no botão "Play" utilizando emuladores configurados (RetroArch, Kega Fusion, etc.).
- **Capas Automáticas:** Busca e download automático de capas oficiais dos jogos.
- **Busca e Filtros:** Pesquisa rápida por nome, ordenação por data, avaliação e favoritos.
- **Histórico e Estatísticas:** Contador de vezes jogadas e data da última partida.

---

## 🚀 Como Executar

### Pré-requisitos
- **Python 3.10+** instalado no sistema.
- Emuladores configurados (ex: RetroArch ou emuladores dedicados).

### Inicialização Rápida no Windows
Basta dar dois cliques no arquivo:
```cmd
start.bat
```
O script cuidará da criação do ambiente virtual, instalação de dependências e abrirá automaticamente o navegador em `http://localhost:8080`.

---

## ⚙️ Configuração dos Emuladores

As pastas de ROMs e executáveis dos emuladores são definidas no arquivo `config.json`.
Exemplo de configuração para o RetroArch:

```json
"Nintendo DS": {
  "name": "RetroArch",
  "path": "C:/RetroArch-Win64/retroarch.exe",
  "args": "-L \"C:/RetroArch-Win64/cores/melonds_libretro.dll\" \"{rom}\""
}
```

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python, Flask, SQLite.
- **Frontend:** HTML5, CSS3 moderno, Vanilla JavaScript.
