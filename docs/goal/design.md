# FaceFusion Modernizado — Design System

## 1. Overview

O sistema de design do **FaceFusion Modernizado** adota uma abordagem **Premium Dark Mode**, focada na clareza técnica, no alto contraste e na estética voltada para criadores de conteúdo e profissionais de inteligência computacional. Inspirado em consoles modernos de desenvolvimento (como Vercel, Linear e interfaces de hardware avançado da NVIDIA), a UI combina fundos escuros profundos, superfícies translúcidas (efeito glassmorphism), divisórias finas e acentos de cor vibrantes (vermelho vivo e verde esmeralda) para sinalizar ação e status.

A tipografia limpa baseada no sistema ou na fonte Geist fornece leitura precisa de parâmetros, enquanto sombras discretas de elevação criam uma forte hierarquia tridimensional em telas de dashboard.

---

## 2. Paleta de Cores (Color Tokens)

As cores são estruturadas em torno de tons escuros para o layout e cores semânticas focadas em status e alertas:

### Cores Base & Neutras
* **`background` (`#0a0a0a`)**: Fundo geral do cockpit e da página, oferecendo contraste ideal e redução de fadiga visual em longas sessões de processamento.
* **`surface` (`#09090b` / `bg-zinc-950/40`)**: Utilizada em cards de parâmetros, listas e barras laterais. O uso de opacidade parcial (`/40`) com desfoque de fundo (`backdrop-blur-xl`) confere o visual translúcido premium.
* **`border` (`#18181b` / `border-zinc-900`)**: Divisórias discretas e finas de `1px` que separam elementos sem causar poluição visual.
* **`text-primary` (`#ededed`)**: Texto principal de alta legibilidade, com contraste confortável sobre o fundo escuro.
* **`text-secondary` (`#a1a1aa` / `text-zinc-400`)**: Usada em rótulos, legendas, caminhos de arquivo e informações secundárias.

### Cores de Destaque & Ação
* **`brand-accent` (`#ef4444` / `bg-red-600`)**: Vermelho vibrante, cor identidade do FaceFusion. Usado para botões de CTA primários, bordas de indicadores ativos e marcações de logo.
* **`brand-hover` (`#dc2626` / `bg-red-700`)**: Tom mais escuro do acento para feedbacks de hover.

### Cores Semânticas de Status
* **`Queued / Idle` (`#3b82f6` / `text-blue-400`)**: Azul para sinalizar tarefas aguando execução ou em modo ocioso.
* **`Processing` (`#f59e0b` / `text-amber-500`)**: Amarelo âmbar para tarefas ativas no Worker, com efeito de pulsação suave.
* **`Completed` (`#10b981` / `text-emerald-500`)**: Verde esmeralda para sinalizar tarefas concluídas com sucesso.
* **`Failed` (`#ef4444` / `text-red-500`)**: Vermelho para sinalizar falhas, erros de sintaxe ou timeouts de processamento de hardware.

---

## 3. Tipografia (Typography)

Para manter a performance de carregamento offline-first (sem downloads de fontes na web), a tipografia baseia-se na fonte Geist ou nas fontes nativas de sistema (`sans-serif`):

* **`Font Family`**: `system-ui, -apple-system, sans-serif`
* **`Font Mono`**: `monospace` (usado para códigos de identificação de jobs, coordenadas, logs e tempos).
* **`Hierarquia de Textos`**:
  * **Título Logo**: `font-extrabold`, `tracking-tight`, tamanho `xl` (20px).
  * **Títulos de Seção**: `font-bold`, tamanho `lg` (18px) ou `base` (16px).
  * **Rótulos e Parâmetros**: `font-semibold` ou `medium`, tamanho `sm` (14px).
  * **Valores / Inputs**: `font-mono`, tamanho `sm` (14px) ou `xs` (12px).
  * **Mensagens de Erro / Logs**: `font-mono`, tamanho `xs` (12px), com espaçamento confortável de linha (`leading-relaxed`).

---

## 4. Layout & Espaçamento

O layout é desenhado em formato de grade flexível com navegação lateral:
* **Sidebar**: Fixa na lateral esquerda, largura de `240px` (`w-64`), com borda sutil à direita e fundo cinza-escuro translúcido. Os itens selecionados exibem uma borda vertical esquerda de `2px` vermelha (`border-red-500`) e fundo destacado.
* **Header Superior**: Altura fixa de `80px` (`h-20`), contendo barra de pesquisa unificada e painel de telemetria de hardware à direita.
* **Conteúdo Principal**: Margens de `32px` (`p-8`), com rolagem vertical independente na área de trabalho e grid adaptativo para telas grandes.

---

## 5. Elevação, Formas e Bordas

* **Bordas Arredondadas (Border Radius)**:
  * Badges e Filtros: Arredondado total (`rounded-full`) para dar aspecto oval moderno.
  * Inputs, Botões e Items de Menu: Arredondado médio (`rounded-lg` / `8px`) para melhor encaixe ergonômico.
  * Cards e Divisor do Comparador: Arredondado grande (`rounded-xl` / `12px`) para dar sensação de invólucro moderno.
* **Sombra de profundidade**:
  * Cards e painéis utilizam borda fina e sombra imperceptível sobre o fundo escuro (`box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1)`).
  * O indicador de divisor de vídeo (slide comparador) tem sombra profunda e borda branca de destaque para facilitar a manipulação.

---

## 6. Componentes Visuais Chave

### 1. Cards de Mídia (Upload Areas)
* **Estado Vazio**: Borda tracejada (`border-dashed`) com cor cinza escura, ícone centralizado de upload, e transição suave no hover para borda vermelha translúcida e fundo levemente avermelhado.
* **Estado Preenchido**: Imagem ou vídeo ocupando a área útil, com máscara gradiente preta em hover revelando botões de exclusão ("Trash icon") e substituição.

### 2. Comparador Deslizante (Before/After)
* Dois elementos de vídeo/imagem sobrepostos em posição absoluta.
* O divisor vertical é uma linha de `2px` branca com um pegador central circular (`w-8 h-8` com ícone de seta ou barra dupla), que o usuário pode arrastar horizontalmente.
* Conforme o divisor se move, o recorte de largura (`clip-path` ou `width` dinâmico) do elemento superior é reajustado em tempo real.

### 3. Sliders de Parâmetros
* Barra de alcance (`input type="range"`) estilizada com preenchimento cinza e indicador (thumb) vermelho redondo.
* O valor numérico atualizado é sempre exibido no canto superior direito do parâmetro em tipografia mono e cor acentuada vermelha.
