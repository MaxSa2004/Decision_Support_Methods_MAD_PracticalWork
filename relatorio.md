# Relatório do Projeto Prático - Vigilância de Partições Retangulares

**Unidade Curricular:** Métodos de Apoio à Decisão\
**Alunos:** Orlando Soares (up202303606), Maximiliano Sá (up202305979), Paulo Lin (up202304528)\
**Ano Letivo:** 2025/2026

---

# 1. Introdução

O presente relatório descreve a resolução do projeto prático proposto na unidade curricular de Métodos de Apoio à Decisão, subordinado ao tema **Vigilância de Partições Retangulares**.

O problema em estudo consiste em determinar a colocação ótima de guardas em vértices de uma partição retangular, de forma a assegurar a cobertura visual de todos os retângulos da partição, ou apenas de um subconjunto destes, minimizando simultaneamente o número de guardas utilizados.

Este problema insere-se no domínio da **otimização combinatória**, apresentando semelhanças diretas com o problema clássico de *Set Covering*, no qual se pretende selecionar o menor número de conjuntos capazes de cobrir um universo de elementos.

Neste contexto:

- cada vértice da partição corresponde a uma possível localização para um guarda;
- cada guarda cobre um conjunto de retângulos incidentes;
- o objetivo global é encontrar a combinação mínima de vértices cuja união de coberturas satisfaça os requisitos de vigilância.

Ao longo do trabalho foram exploradas múltiplas metodologias de resolução, permitindo comparar paradigmas heurísticos e exatos de apoio à decisão.

Foram estudadas as seguintes abordagens:

- Estratégias Greedy;
- Programação Inteira Binária;
- Programação por Restrições com MAC e AC-3;
- Resolução em Google OR-Tools;
- Programação Dinâmica;
- Extensões do problema com guardas coloridos e guardas de alcance ampliado.

---

# 2. Modelação Formal do Problema

Considere-se uma partição retangular $\Pi = \{R_1, R_2, \dots, R_n\}$, composta por $n$ retângulos, e um conjunto de vértices geométricos $V = \{v_1, v_2, \dots, v_m\}$.

Cada vértice pode potencialmente receber um guarda.

Um guarda colocado num vértice $v_i$ vigia todos os retângulos incidentes a esse vértice.

## 2.1 Matriz de Cobertura

Define-se uma matriz binária de cobertura $A \in \{0,1\}^{m \times n}$:

$$
A[i][j] =
\begin{cases}
1, & \text{se o vértice } v_i \text{ cobre o retângulo } R_j \\
0, & \text{caso contrário}
\end{cases}
$$

Esta matriz constitui a representação central utilizada por todos os algoritmos implementados.

## 2.2 Objetivo Global

Pretende-se determinar um subconjunto mínimo de vértices:

$$
G \subseteq V
$$

que satisfaça:

$$
\bigcup_{v \in G} covers(v) \supseteq \Pi'
$$

onde $\Pi'$ representa o conjunto de retângulos a vigiar.

## 2.3 Cobertura Parcial

O modelo suporta igualmente o caso em que apenas um subconjunto $\Pi' \subset \Pi$ tem de ser coberto. Neste caso, os algoritmos recebem um parâmetro `required` com os índices dos retângulos obrigatórios:

$$
\Pi' = \{ R_j \mid j \in \texttt{required} \}
$$

Quando `required` é omitido, assume-se $\Pi' = \Pi$ (cobertura total), preservando o comportamento original. Esta generalização foi implementada em todos os solvers sem alterar a interface existente.

## 2.4 Complexidade: Cobertura Total vs Cobertura de Subconjunto (na teoria)

É importante distinguir dois cenários conceptualmente diferentes:

- **Cobertura total**: quando o requisito é cobrir a totalidade dos elementos-alvo do modelo, o problema pode, em formulações estruturadas específicas, ser reduzido a um problema clássico com algoritmo polinomial (por exemplo, uma redução para um problema em grafos bipartidos).
- **Cobertura parcial (subconjunto)**: quando apenas um subconjunto de elementos é obrigatório, essa redução deixa, em geral, de ser válida. O problema resultante mantém a natureza combinatória difícil e é tipicamente NP-hard.

Esta diferença justifica a opção por duas famílias de métodos ao longo do projeto:

- métodos de otimização exata (ILP/DP) para garantir optimalidade quando a dimensão o permite;
- métodos heurísticos ou de satisfazibilidade (greedy/CSP) para obter soluções viáveis rapidamente quando a variante parcial conduz a instâncias computacionalmente mais exigentes.

Do ponto de vista prático, o greedy não garante solução ótima no caso NP-hard, mas constitui uma estratégia de aproximação eficaz, com boa relação entre qualidade da solução e tempo de execução.

---

# 3. Estratégias Greedy

## 3.1 Motivação

As estratégias greedy foram utilizadas como primeira abordagem heurística devido à sua simplicidade de implementação e reduzido custo computacional.

Estas heurísticas constroem a solução incrementalmente, tomando em cada passo a decisão local aparentemente mais vantajosa.

## 3.2 Heurística de Máxima Cobertura Residual

Em cada iteração é selecionado o vértice que cobre o maior número de retângulos ainda não vigiados.

### Pseudocódigo

```text
GreedyCoverage(U, V):
    guards <- {}
    while U não vazio:
        escolher v em V que maximiza |covers(v) ∩ U|
        guards <- guards ∪ {v}
        U <- U \ covers(v)
    return guards
```

## 3.3 Complexidade

Sejam:

- $m$ o número de vértices;
- $n$ o número de retângulos.

A cada iteração é necessário avaliar a cobertura residual de todos os vértices, resultando numa complexidade aproximada:

$$
O(m \cdot n)
$$

por iteração, conduzindo na prática a tempos de execução muito baixos.

## 3.4 Discussão

A abordagem greedy revelou-se adequada para produzir soluções, mesmo em instâncias de grande dimensão. Contudo, por não considerar consequências globais futuras, conduz frequentemente a soluções subótimas.

Este comportamento torna-se particularmente relevante no cenário de cobertura parcial (subconjunto obrigatório), onde a estrutura do problema deixa de permitir reduções polinomiais diretas e a dificuldade combinatória aumenta. Nesses casos, as heurísticas greedy funcionam como algoritmos de aproximação: sacrificam garantia de optimalidade, mas devolvem soluções viáveis em tempos reduzidos.

Apesar disso, os resultados experimentais mostram que, para instâncias muito grandes, o OR-Tools (CP-SAT) foi mais eficiente na prática do que o greedy.

---

# 4. Programação Inteira Binária com OR-Tools

## 4.1 Formulação Matemática

Foi modelado o problema como um programa linear inteiro binário.

### Variáveis de decisão

$$
x_i =
\begin{cases}
1, & \text{se existe guarda no vértice } i \\
0, & \text{caso contrário}
\end{cases}
$$

### Função objetivo

$$
\min \sum_{i=1}^{m} x_i
$$

### Restrições de cobertura

Para cada retângulo $R_j$:

$$
\sum_{i : A[i][j]=1} x_i \ge 1
$$

Cada retângulo deve ser coberto por pelo menos um guarda.

## 4.2 Complexidade

O modelo contém $m$ variáveis binárias e $O(n)$ restrições de cobertura (uma por retângulo).

A formulação é NP-difícil por equivalência ao problema de Set Cover.

No entanto, solvers modernos conseguem resolver eficientemente instâncias de dimensão moderada.

## 4.3 Implementação

A implementação foi realizada em Python utilizando o módulo CP-SAT do Google OR-Tools, que permite:

- criação de variáveis binárias;
- adição de restrições lineares;
- otimização da função objetivo.

## 4.4 Desempenho
Este solver demonstrou excelente eficiência na obtenção da solução ótima, apresentando
tempos de execução residuais.

---

# 5. Programação por Restrições, MAC com AC-3

## 5.1 Formulação CSP

Cada vértice é modelado como uma variável booleana:

$$
X_i \in \{0,1\}
$$

Para cada retângulo gera-se uma restrição disjuntiva:

$$
\bigvee_{i \in C(r)} X_i
$$

onde $C(r)$ representa o conjunto de vértices que cobrem o retângulo $r$.

## 5.2 Backtracking com MAC

Foi implementado um algoritmo de procura em profundidade com:

- seleção de variáveis por MRV;
- atribuição binária;
- manutenção de consistência de arcos após cada decisão.

## 5.3 Algoritmo AC-3

Após cada atribuição é executado AC-3 sobre pares (variável, restrição), removendo valores sem suporte na restrição de cobertura.

### Pseudocódigo

```text
AC3(queue):
    enquanto queue não vazio:
        remover (var, rect)
        se Revise(var, rect):
            se domínio(var) vazio -> falha
            adicionar pares vizinhos afetados

Revise(var, rect):
    revisado = falso
    para cada valor em domínio(var):
        se não houver suporte na restrição "pelo menos um vértice cobre rect":
            remover valor de domínio(var)
            revisado = verdadeiro
    retornar revisado
```

## 5.4 Vantagens

Comparativamente ao backtracking puro, a propagação MAC permitiu uma redução substancial do espaço de procura.

## 5.5 Nota sobre Optimalidade do CSP Implementado

O solver CSP implementado (`csp_mac.py`) resolve um problema de **satisfazibilidade**: encontra uma atribuição válida que cobre todos os retângulos obrigatórios, mas **não** inclui função objetivo para minimizar o número de guardas.

Assim, a primeira solução viável devolvida pela procura pode usar mais guardas do que outros métodos (incluindo greedy ou ILP). Para obter optimalidade em CSP seria necessário acrescentar um mecanismo de otimização (por exemplo, branch-and-bound sobre $\sum_i X_i$ ou pesquisa iterativa com limite no número de guardas).

---

# 6. Programação Dinâmica

## 6.1 Definição do Estado

Seja $S$ um subconjunto de retângulos já cobertos.

Define-se:

$$
DP[S] = número mínimo de guardas necessários para cobrir S
$$

## 6.2 Transição

Para cada vértice $v$:

$$
DP[S \cup covers(v)] = \min(DP[S \cup covers(v)], DP[S] + 1)
$$

## 6.3 Análise

Esta abordagem garante a obtenção da solução ótima.

Todavia, apresenta complexidade:

$$
O(2^n \cdot m)
$$

(onde $n$ é o número de retângulos e $m$ o número de vértices que podem representar guardas) sendo por isso apenas prática para instâncias pequenas.

---

# **7. Extensões do Problema**

## **7.1 Guardas com cores (coloração de conflitos)**

Nesta extensão introduz-se uma restrição adicional de compatibilidade entre guardas. Em particular, dois guardas não podem partilhar a mesma cor caso exista pelo menos um retângulo que seja observado simultaneamente por ambos. Esta condição modela situações em que a presença conjunta de dois guardas no mesmo domínio de vigilância implica conflito, exigindo a sua diferenciação através de cores.

Após a obtenção de uma solução mínima para o problema original de colocação de guardas, constrói-se um grafo de conflitos $G=(V,E)$, onde:

- cada vértice representa um guarda colocado;
- existe uma aresta entre dois guardas se estes partilham a vigilância de pelo menos um retângulo.

Formalmente, para guardas $g_i$ e $g_j$, existe uma aresta $(g_i,g_j)$ se:

$$
\exists r \in \Pi : r \in C(g_i) \land r \in C(g_j)
$$

onde $C(g)$ representa o conjunto de retângulos cobertos pelo guarda $g$.

O problema reduz-se então a um problema clássico de coloração de grafos, cujo objetivo é atribuir cores aos vértices de forma a que vértices adjacentes tenham cores diferentes, minimizando o número total de cores utilizadas.

Foi implementado um algoritmo de coloração exata por backtracking com poda (branch-and-bound), que explora sistematicamente as atribuições possíveis de cores e elimina ramos cuja solução parcial já excede a melhor solução encontrada.

### **Complexidade**

O problema de coloração mínima de grafos é NP-completo. O algoritmo implementado tem complexidade exponencial no pior caso:

$$
O(k^n)
$$

onde $n$ é o número de guardas e $k$ o número de cores utilizadas na solução corrente. No entanto, a ordenação dos vértices por grau e a poda por limite superior reduzem significativamente o espaço de pesquisa na prática.

---

## **7.2 Guardas com maior alcance**

Nesta extensão considera-se um parâmetro de alcance $D$, que permite a um guarda vigiar não apenas os retângulos diretamente incidentes no seu vértice, mas também retângulos adjacentes até uma distância de grafo no máximo $D$.

Para modelar esta extensão, foi construído o grafo de adjacência entre retângulos (grafo dual), onde:

- cada nó representa um retângulo;
- existe uma aresta entre dois retângulos se estes partilham pelo menos um vértice.

Formalmente:

$$
(r_i,r_j) \in E \iff V(r_i) \cap V(r_j) \neq \emptyset
$$

A expansão da cobertura de um guarda é então obtida através de uma pesquisa em largura (BFS) neste grafo, partindo dos retângulos diretamente observados pelo guarda e explorando vizinhos até profundidade $D$.

O conjunto final de retângulos cobertos por um guarda corresponde à união dos retângulos alcançados pela BFS a partir dos seus retângulos incidentes.

Este conjunto expandido substitui a cobertura original no modelo de otimização, permitindo que o problema original de set cover seja resolvido com uma matriz de incidência modificada.

### **Complexidade**

A construção do grafo de retângulos tem custo:

$$
O(n^2 \cdot m)
$$

onde $n$ é o número de retângulos e $m$ o número médio de vértices por retângulo.

A BFS para cada guarda tem custo:

$$
O(|V| + |E|)
$$

Como esta expansão é feita antes da resolução do problema principal, o custo total depende do solver escolhido (tipicamente exponencial para métodos exatos como DP ou ILP), mas a fase de pré-processamento é polinomial.

---

# 8. Descrição da Implementação

A implementação foi desenvolvida integralmente em Python, organizando-se da seguinte maneira:

- `main.py`, leitura da partição, construção da matriz de cobertura e print dos resultados do método escolhido;
- `greedy.py`, heurísticas greedy;
- `integer_solver.py`, modelo de programação inteira - Google OR-Tools;
- `csp_mac.py`, backtracking com MAC + AC3;
- `dynamic.py`, programação dinâmica;
- `extensions.py`, guardas coloridos e alcance D.
- `performance_benchmarker.py`, benchmark unificado (solvers base e extensões), com geração de `required` aleatório por rácio e desativação automática de métodos após timeout.

Esta modularização facilitou a reutilização da mesma matriz de cobertura por todos os paradigmas de resolução.

Todos os solvers implementados suportam cobertura parcial através do parâmetro `required`, que recebe os índices (base 0) dos retângulos obrigatórios. Quando omitido, é assumida cobertura total, conforme descrito na Secção 2.3.

---

# 9. Resultados Experimentais

Para avaliar o desempenho das abordagens implementadas, foi utilizado o script unificado `performance_benchmarker.py`, que executa métodos base e extensões no mesmo pipeline experimental.

Configuração usada (conforme `benchmarks_results.txt`):

- `suite=all`;
- `ratios=[0.1, 0.25, 0.5, 0.75, 1.0]`;
- `samples_per_ratio=3`;
- `repetitions=1`;
- `TIME_LIMIT=60s`.

Como `ratio=1.0` é equivalente à cobertura total, este rácio é o mais relevante para comparação direta com o problema original.

## 9.1 Resultados Obtidos (ratio = 1.0)

| Instância             | Dynamic | Greedy     | Integer    | CSP        | Coloring   | Expand     |
| --------------------- | ------- | ---------- | ---------- | ---------- | ---------- | ---------- |
| `10rect_5instances`   | 0.686573 s | 0.659276 s | 0.654564 s | 0.632468 s | 0.648752 s | 0.649922 s |
| `30rect_5instances`   | n/a (desativado) | 0.764849 s | 0.698455 s | 0.659104 s | 0.659815 s | 0.651680 s |
| `50rect_5instances`   | n/a | 0.893004 s | 0.749201 s | 0.674262 s | 0.677816 s | 0.668987 s |
| `100rect_5instances`  | n/a | 0.669252 s | 0.705239 s | 0.660147 s | 0.694367 s | 0.693594 s |
| `500rect_5instances`  | n/a | 2.155261 s | 0.987748 s | 0.979763 s | 0.994068 s | 0.992772 s |
| `1000rect_5instances` | n/a | 15.593268 s | 2.227116 s | n/a (desativado) | 2.329794 s | 1.907156 s |

No próprio benchmark, os métodos foram removidos das iterações seguintes após timeout:

- `dynamic` (timeout em `30rect_5instances`, `ratio=0.25`);
- `csp` (timeout em `1000rect_5instances`, `ratio=0.10`).

## 9.2 Análise dos Resultados

No cenário equivalente ao problema original (`ratio=1.0`):

- **Greedy** mantém boa simplicidade, mas degrada significativamente em instâncias grandes (15.59 s em 1000 retângulos);
- **Integer (CP-SAT)** mantém desempenho robusto e controlado até 1000 retângulos (2.23 s), preservando qualidade da solução;
- **CSP (MAC+AC3)** é competitivo em pequena/média escala, mas não é robusto em grande dimensão; além disso, como é um solver de satisfazibilidade (sem minimização explícita), pode devolver soluções com mais guardas;
- **Dynamic** confirma limitação exponencial, tornando-se rapidamente impraticável;
- **Coloring** fica naturalmente próximo do custo de `integer` acrescido do custo de coloração;
- **Expand** reduz substancialmente o número médio de guardas graças à cobertura ampliada e teve bom desempenho temporal.

Assim, para cobertura total, os resultados continuam a recomendar **CP-SAT** como alternativa mais estável entre qualidade e escalabilidade.

## 9.3 Comportamento em Partial Set Cover (`ratio < 1`)

Para além do caso `ratio=1.0`, os resultados confirmam um comportamento coerente em cobertura parcial:

- quando `required_ratio` aumenta, o número médio de guardas cresce em todos os métodos (como esperado);
- a diferença entre **greedy** e **integer (CP-SAT)** aumenta com a dimensão da instância;
- o **CP-SAT** mantém melhor robustez temporal para rácios intermédios/altos em instâncias grandes;
- o **csp** tende a usar mais guardas do que integer/greedy porque procura apenas uma solução viável (não mínima), e perde robustez em larga escala;
- a extensão **expand** reduz fortemente o número de guardas, por aumentar o alcance efetivo de cada guarda.

Exemplo representativo em `1000rect_5instances`:

- `ratio=0.10`: greedy = 1.022637 s, integer = 0.772197 s;
- `ratio=0.50`: greedy = 5.691275 s, integer = 1.149051 s;
- `ratio=0.75`: greedy = 10.535604 s, integer = 0.942098 s;
- `ratio=1.00`: greedy = 15.593268 s, integer = 2.227116 s.

Ou seja, mesmo no cenário parcial, os dados do benchmark corroboram que, na prática, **OR-Tools (CP-SAT)** é a alternativa mais eficiente para instâncias grandes, enquanto o greedy é útil sobretudo como baseline heurístico rápido.

---

# 10. Conclusão

O presente projeto permitiu estudar e comparar múltiplas metodologias de apoio à decisão aplicadas ao problema de vigilância de partições retangulares, um problema de cobertura combinatória com relevância teórica e prática.

Os resultados experimentais confirmam as expectativas teóricas de forma clara. A **Programação Dinâmica** mostrou-se impraticável para instâncias de dimensão moderada/grande, sofrendo timeout no benchmark unificado. O **CSP com MAC+AC3**, embora competitivo em instâncias pequenas e médias, também apresenta limitações de escalabilidade em dimensão muito elevada e, na versão implementada, não garante mínimo número de guardas por ser um solver de satisfazibilidade. O **Greedy**, apesar de simples e funcional, revelou degradação acentuada no caso de cobertura total (`ratio=1.0`), atingindo 15.59 s para 1000 retângulos.

A **Programação Inteira com OR-Tools (CP-SAT)** destacou-se novamente como a abordagem mais robusta: no cenário equivalente à cobertura total (`ratio=1.0`) manteve desempenho na ordem dos 2 s para 1000 retângulos, com garantia de optimalidade. É a escolha recomendada para instâncias em que se exija simultaneamente qualidade e escalabilidade.

Em suma:

- **OR-Tools (CP-SAT)** - solução preferencial: ótima, rápida e escalável;
- **Greedy** - útil como heurística inicial;
- **CSP com MAC+AC3** - adequado para encontrar soluções viáveis em instâncias moderadas, mas sem garantia de mínimo número de guardas e com limites em grande escala;
- **Programação Dinâmica** - referência de optimalidade, restrita a instâncias pequenas.

As extensões implementadas - coloração de guardas e alcance ampliado - demonstraram ainda que a abstração central do projeto, a matriz de cobertura, é suficientemente flexível para acomodar variantes mais ricas do problema sem alterar a arquitectura de resolução.

---

# 11. Adaptação ao Formato das Instâncias

O gerador de instâncias utilizado no projeto produz ficheiros no formato:

```text
k = <int>
<id> <m> x1 y1 x2 y2 ... xm ym
```

onde:

- `k` representa o número de retângulos existentes na instância;
- `id` representa o identificador do retângulo, variando entre `1` e `k`;
- `m` representa o número de vértices do retângulo;
- os pares `(xi, yi)` representam as coordenadas dos vértices.

Exemplo:

```text
8
1 4 0 6 4 6 4 7 0 7
2 4 4 6 8 6 8 7 4 7
...
```

Cada linha define um retângulo da partição.

## 11.1 Parser das Instâncias

Foi desenvolvido um parser responsável por:

- ler múltiplas instâncias no mesmo ficheiro;
- extrair vértices únicos;
- construir os retângulos;
- gerar automaticamente a matriz de cobertura.

```python
class Rectangle:
    def __init__(self, rid, vertices):
        self.id = rid
        self.vertices = vertices


class Instance:
    def __init__(self, k):
        self.k = k
        self.rectangles = []

        # ordered unique vertices
        self.vertices = []


def parse_instances(filename):
    with open(filename, 'r') as f:
        raw_lines = [ln.strip() for ln in f if ln.strip()]

    instances = []
    i = 0

    # optional number of instances
    n = None
    if (
        i + 1 < len(raw_lines)
        and len(raw_lines[i].split()) == 1
        and len(raw_lines[i + 1].split()) == 1
    ):
        try:
            n = int(raw_lines[i])
            i += 1
        except ValueError:
            pass

    instances_parsed = 0

    while i < len(raw_lines) and (n is None or instances_parsed < n):

        # instance size k
        if len(raw_lines[i].split()) != 1:
            raise ValueError(
                f"Expected instance grid size k at line {i+1}: '{raw_lines[i]}'"
            )

        k = int(raw_lines[i])
        inst = Instance(k)
        i += 1

        # read rectangles
        while i < len(raw_lines):

            parts = raw_lines[i].split()

            # next instance starts
            if len(parts) == 1:
                break

            try:
                nums = list(map(int, parts))
            except ValueError:
                raise ValueError(
                    f"Non-integer token on line {i+1}: '{raw_lines[i]}'"
                )

            rid = nums[0]
            m = nums[1]
            coords = nums[2:]

            if len(coords) != 2 * m:
                raise ValueError(
                    f"Expected {2*m} coord values for face {rid}, "
                    f"got {len(coords)} on line {i+1}"
                )

            vertices = []

            for j in range(0, len(coords), 2):
                v = (coords[j], coords[j + 1])

                vertices.append(v)

                # keep unique ordered vertices
                if v not in inst.vertices:
                    inst.vertices.append(v)

            inst.rectangles.append(Rectangle(rid, vertices))
            i += 1

        instances.append(inst)
        instances_parsed += 1

    return instances
```



Desta forma todos os algoritmos implementados podem ser executados diretamente sobre as instâncias produzidas pelo gerador fornecido.

---

# 12. Implementações dos Algoritmos

## 12.1 Implementação Greedy em Python

```python
class GreedySolver:
    def __init__(self, coverage_matrix, required=None):
        self.A = coverage_matrix
        self.num_vertices = len(coverage_matrix)
        self.num_rectangles = len(coverage_matrix[0])
        # required: indices of rectangles that must be covered (None = all)
        self.required = set(required) if required is not None else set(range(self.num_rectangles))

    def solve(self):
        uncovered = set(self.required)
        guards = []

        while uncovered:
            best_vertex = None
            best_cover = set()

            for v in range(self.num_vertices):
                current_cover = {r for r in uncovered if self.A[v][r] == 1 and r in self.required}
                if len(current_cover) > len(best_cover):
                    best_cover = current_cover
                    best_vertex = v

            guards.append(best_vertex)
            uncovered -= best_cover

        return guards
```

## 12.2 Implementação de Programação Inteira com OR-Tools

```python
from ortools.sat.python import cp_model

class IntegerSolver:
    def __init__(self, coverage_matrix, required=None):
        self.A = coverage_matrix
        self.m = len(coverage_matrix)
        self.n = len(coverage_matrix[0])
        # required: indices of rectangles that must be covered (None = all)
        self.required = list(required) if required is not None else list(range(self.n))

    def solve(self):
        model = cp_model.CpModel()
        x = [model.NewBoolVar(f'x{i}') for i in range(self.m)]

        for j in self.required:
            model.Add(sum(x[i] for i in range(self.m) if self.A[i][j] == 1) >= 1)

        model.Minimize(sum(x))

        solver = cp_model.CpSolver()
        solver.Solve(model)

        return [i for i in range(self.m) if solver.Value(x[i]) == 1]
```

## 12.3 Implementação MAC + AC3

Nota: esta implementação procura uma atribuição viável e termina na primeira solução encontrada. Não há função objetivo para minimizar o número total de guardas.

```python
from collections import deque

class MACSolver:
    def __init__(self, coverage_matrix, required=None):
        self.A = coverage_matrix
        self.m = len(coverage_matrix)
        self.n = len(coverage_matrix[0]) if self.m > 0 else 0
        self.required = list(required) if required is not None else list(range(self.n))

        self.rect_to_vars = {
            r: [i for i in range(self.m) if self.A[i][r] == 1]
            for r in self.required
        }

        self.var_to_rects = {i: [] for i in range(self.m)}
        for r, vars_covering_r in self.rect_to_vars.items():
            for i in vars_covering_r:
                self.var_to_rects[i].append(r)

    def _initial_domains(self):
        return [set([0, 1]) for _ in range(self.m)]

    def _has_support(self, var, value, rect, domains):
        if self.A[var][rect] == 1 and value == 1:
            return True
        for other in self.rect_to_vars[rect]:
            if other != var and 1 in domains[other]:
                return True
        return False

    def _revise(self, var, rect, domains):
        revised = False
        for value in list(domains[var]):
            if not self._has_support(var, value, rect, domains):
                domains[var].remove(value)
                revised = True
        return revised

    def _ac3(self, domains, queue=None):
        if queue is None:
            queue = deque((var, r) for r, scope in self.rect_to_vars.items() for var in scope)
        else:
            queue = deque(queue)

        while queue:
            var, rect = queue.popleft()
            if self._revise(var, rect, domains):
                if not domains[var]:
                    return False

                for other_rect in self.var_to_rects[var]:
                    for other_var in self.rect_to_vars[other_rect]:
                        if other_var != var:
                            queue.append((other_var, other_rect))

        return True

    def _backtrack_mac(self, domains):
        if all(len(dom) == 1 for dom in domains):
            assignment = [next(iter(dom)) for dom in domains]
            if all(any(assignment[i] == 1 for i in self.rect_to_vars[r]) for r in self.required):
                return assignment
            return None

        var = min((i for i in range(self.m) if len(domains[i]) > 1), key=lambda i: len(domains[i]), default=None)
        if var is None:
            return None

        for value in [0, 1]:
            if value not in domains[var]:
                continue

            new_domains = [set(dom) for dom in domains]
            new_domains[var] = set([value])

            local_queue = []
            for rect in self.var_to_rects[var]:
                for scope_var in self.rect_to_vars[rect]:
                    local_queue.append((scope_var, rect))

            if self._ac3(new_domains, local_queue):
                result = self._backtrack_mac(new_domains)
                if result is not None:
                    return result

        return None

    def solve(self):
        if any(len(self.rect_to_vars[r]) == 0 for r in self.required):
            return None

        domains = self._initial_domains()
        if not self._ac3(domains):
            return None

        return self._backtrack_mac(domains)
```

## 12.4 Implementação de Programação Dinâmica

```python
class DPSolver:
    def __init__(self, coverage_sets, n_rectangles, required=None):
        self.coverage_sets = coverage_sets
        self.n = n_rectangles
        # required: indices of rectangles that must be covered (None = all)
        required_indices = required if required is not None else range(n_rectangles)
        self.full = 0
        for r in required_indices:
            self.full |= (1 << r)

    def solve(self):
        from collections import deque

        full = self.full
        dp = {0: []}
        queue = deque([0])

        while queue:
            state = queue.popleft()
            guards = dp[state]

            if state & full == full:
                return guards

            for v, cov in enumerate(self.coverage_sets):
                new_state = state
                for r in cov:
                    new_state |= (1 << r)

                if new_state not in dp or len(dp[new_state]) > len(guards)+1:
                    dp[new_state] = guards + [v]
                    queue.append(new_state)
```

## 12.5 Implementação da Extensão Guardas Coloridos

```python
def build_conflict_graph(selected_guards, coverage_matrix):

    graph = {
        g: set()
        for g in selected_guards
    }

    n_rectangles = len(coverage_matrix[0])

    for r in range(n_rectangles):

        guards_covering = [
            g
            for g in selected_guards
            if coverage_matrix[g][r] == 1
        ]

        for i in range(len(guards_covering)):
            for j in range(i + 1, len(guards_covering)):

                g1 = guards_covering[i]
                g2 = guards_covering[j]

                graph[g1].add(g2)
                graph[g2].add(g1)

    return graph

def exact_coloring(graph):

    nodes = list(graph.keys())

    # order nodes by degree (important for pruning)
    nodes.sort(key=lambda x: len(graph[x]), reverse=True)

    n = len(nodes)

    best_coloring = {}
    best_k = float("inf")

    coloring = {}

    def backtrack(i, used_colors):

        nonlocal best_coloring, best_k

        # pruning
        if used_colors >= best_k:
            return

        if i == n:
            best_coloring = coloring.copy()
            best_k = used_colors
            return

        node = nodes[i]

        forbidden = {
            coloring[nbr]
            for nbr in graph[node]
            if nbr in coloring
        }

        for c in range(used_colors):

            if c not in forbidden:
                coloring[node] = c
                backtrack(i + 1, used_colors)
                del coloring[node]

        # try new color
        coloring[node] = used_colors
        backtrack(i + 1, used_colors + 1)
        del coloring[node]

    backtrack(0, 0)

    return best_coloring, best_k
```

## 12.6 Implementação da Extensão Alcance D

```python
def build_rectangle_graph(instance):

    n = len(instance.rectangles)

    graph = {
        i: set()
        for i in range(n)
    }

    for i in range(n):

        ri = set(instance.rectangles[i].vertices)

        for j in range(i + 1, n):

            rj = set(instance.rectangles[j].vertices)

            # adjacent if share at least one vertex
            if ri & rj:

                graph[i].add(j)
                graph[j].add(i)

    return graph


def bfs_expand(rect_graph, start_rectangles, D):

    visited = set(start_rectangles)

    queue = deque()

    for r in start_rectangles:
        queue.append((r, 0))

    while queue:

        node, dist = queue.popleft()

        if dist == D:
            continue

        for neigh in rect_graph[node]:

            if neigh not in visited:

                visited.add(neigh)

                queue.append((neigh, dist + 1))

    return visited


# =========================================================
# Expanded coverage sets for distance D
# =========================================================

def build_expanded_coverage_sets(instance, D):

    rect_graph = build_rectangle_graph(instance)

    vertex_index = {
        v: i
        for i, v in enumerate(instance.vertices)
    }

    coverage_sets = [
        set()
        for _ in instance.vertices
    ]

    # direct coverage
    for rect_idx, rect in enumerate(instance.rectangles):

        for v in rect.vertices:

            vi = vertex_index[v]

            coverage_sets[vi].add(rect_idx)

    # expand with BFS
    expanded = []

    for cov in coverage_sets:

        expanded_cov = bfs_expand(
            rect_graph,
            list(cov),
            D
        )

        expanded.append(sorted(list(expanded_cov)))

    return expanded
```

---

# 13. Algoritmo de Benchmarking

Para medir o desempenho médio dos algoritmos implementados, foi utilizado o script `performance_benchmarker.py`, baseado em execução isolada por processo, limitação temporal por execução e geração de subconjuntos obrigatórios por rácio.

## 13.1 Estratégia de Medição

A metodologia adotada segue os passos:

1. Ler as instâncias de cada ficheiro de entrada;
2. Construir, para cada instância, os conjuntos de cobertura e a matriz binária de cobertura $A$;
3. Gerar subconjuntos `required` para cada rácio de cobertura;
4. Executar cada solver em processo separado (`multiprocessing.Process`);
5. Impor limite máximo de execução de 60 segundos por execução;
6. Em caso de timeout/erro, desativar o método para as iterações seguintes;
7. Repetir várias execuções e calcular métricas médias com `statistics.mean`.

A execução isolada por processo permite interromper algoritmos que excedam o tempo máximo sem bloquear o benchmarking global.

## 13.2 Pseudocódigo

```text
Benchmark(files, solvers, runs, time_limit):
    para cada file em files:
        instances <- parse_instances(file)

        para cada solver em solvers:
            times <- []
            timeout <- falso

            repetir runs vezes:
                para cada instância i em instances:
                    coverage_sets, vertices <- build_coverage_sets(i)
                    A <- build_matrix(coverage_sets, vertices, i.rectangles)

                    t <- run_with_timeout(solver, coverage_sets, A, i, time_limit)
                    se t == TIMEOUT:
                        timeout <- verdadeiro
                        parar
                    adicionar t a times

            se timeout:
                escrever "time limit exceeded"
                desativar solver para iterações seguintes
            senão:
                escrever mean(times)
```

## 13.3 Implementação Utilizada

```python
TIME_LIMIT = 60

def time_solver(solver_func, coverage_sets, A, inst, required, expand_distance, queue):
    try:
        metrics = solver_func(coverage_sets, A, inst, required, expand_distance)
        queue.put(("ok", metrics))
    except Exception as e:
        queue.put(("err", repr(e)))


def benchmark_one(solver_func, coverage_sets, A, inst, required, expand_distance):
    queue = mp.Queue()
    p = mp.Process(
        target=time_solver,
        args=(solver_func, coverage_sets, A, inst, required, expand_distance, queue),
    )

    start = time.perf_counter()
    p.start()
    p.join(TIME_LIMIT)

    if p.is_alive():
        p.terminate()
        p.join()
        return None

    end = time.perf_counter()
    if queue.empty():
        return None

    status, payload = queue.get()
    if status != "ok":
        return None

    return end - start, payload


def benchmark_tasks(solver_func, tasks, repetitions=1, expand_distance=1):
    times = []

    for _ in range(repetitions):
        for coverage_sets, A, inst, required in tasks:
            result = benchmark_one(
                solver_func,
                coverage_sets,
                A,
                inst,
                required,
                expand_distance,
            )
            if result is None:
                return None

            elapsed, _ = result
            times.append(elapsed)

    return {"avg_time": mean(times), "samples": len(times)}

active_solvers = dict(selected_solvers)
for name, solver in list(active_solvers.items()):
    result = benchmark_tasks(solver, tasks, repetitions=args.repetitions, expand_distance=args.expand_distance)
    if result is None:
        # timeout/erro -> desativa para as próximas iterações
        del active_solvers[name]
```

Esta implementação foi a base dos resultados apresentados no Capítulo 9.

---

# 14. Discussão Técnica Global

A implementação prática confirmou que toda a arquitetura do projeto pode ser construída em torno de uma única abstração central: a matriz de cobertura entre vértices e retângulos.

Esta decisão revelou-se particularmente vantajosa porque permitiu reutilizar exatamente os mesmos dados de entrada em todos os paradigmas de resolução estudados.

Em termos computacionais observou-se:

- Greedy: útil como baseline heurístico e para soluções rápidas, mas com degradação marcada em instâncias grandes;
- OR-Tools (CP-SAT): abordagem mais eficiente na prática e mais robusta nos resultados obtidos;
- MAC+AC3: implementação académica rica, competitiva em pequena/média escala, mas com limitações em grande dimensão;
- DP: forte valor teórico, com escalabilidade limitada pela natureza exponencial.
