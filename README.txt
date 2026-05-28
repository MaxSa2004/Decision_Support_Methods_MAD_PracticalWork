Intsruções de execução:

main.py
    - executa o solver selecionado com 1 ficheiro input e imprime os resultados (vertices do guardas)
    
    * executar:
        python3 main.py <input file> <solver_name>

        - <input file> é obrigatório.
        - <solver_name> é opcional.
        - se <solver_name> não for especificado aparece uma lista de solvers disponíveis e o utilizador
            tem de escolher um deles. 

        Solvers Disponíveis:
            - dynamic           (i.e. python3 main.py 30rect_5instances dynamic)
            - greedy            (i.e. python3 main.py 30rect_5instances greedy)
            - weighted_greedy   (i.e. python3 main.py 30rect_5instances weighted_greedy)
            - integer           (i.e. python3 main.py 30rect_5instances integer)
            - csp               (i.e. python3 main.py 30rect_5instances csp)
            - coloring          (i.e. python3 main.py 30rect_5instances coloring)
            - expand            (i.e. python3 main.py 30rect_5instances expand <D>)
        NOTA: expand tem mais um parametro, <D>, se for omitido o programa pede o valor.

    * output:
        o programa imprime:
            - número da instância
            - solver selecionado
            - coordenadas dos guardas
            - número total de guardas

performance_benchmarker.py
    - Este script mede os tempos de execução sobre vários ficheiros de input e diferentes racios de cobertura.

    * executar:
        ** com defaults:
            python3 performance_benchmarker.py

        ** sem defaults:
            - Benchmark options:
                BASE SOLVERS ONLY:
                    python3 performance_benchmarker.py --suite base
                
                EXTENSIONS ONLY:
                    python3 performance_benchmarker.py --suite extensions
                
                ALL SOLVERS
                    python3 performance_benchmarker.py --suite all
            
            - Selecionar solvers especificos:
                BASE SOLVERS:
                    python3 performance_benchmarker.py --base-solvers [dynamic,greedy,integer,csp]
                
                EXTENSION SOLVERS:
                    python3 performance_benchmarker.py --extensions [coloring,expand]
            
            - Selecionar ficheiros de input:
                python3 performance_benchmarker.py --files <input1> <input2> ...
            
            - Coverage Ratios (lista de racios de cobertura obrigatoria em [0,1], separados por virgula):
                python3 performance_benchmarker.py --ratios <r1>,<r2>,<r3>,...

            - Samples per ratio (# de subconjuntos aleatórios gerados):
                python3 performance_benchmarker.py --samples-per-ratio <number>
            
            - Repetições (repetir benchmark <n> vezes):
                python3 performance_benchmarker.py --repetitions <n>

            - Distância de expansão (distância D usada na extensao expand):
                python3 performance_benchmarker.py --expand-distance <D>
            
            - Random seed (seed do gerador aleatorio para reprodutibilidade):
                python3 performance_benchmarker.py --seed <seed>
            
            - Selecionar ficheiro de output:
                python3 performance_benchmarker.py --output <output.txt>

        Exemplo completo (sem defaults):
            python3 performance_benchmarker.py --suite all --base-solvers dynamic,greedy,integer,csp --extensions coloring,expand --files example_inputs/10rect_5instances example_inputs/30rect_5instances --ratios 0.25,0.5,1.0 --samples-per-ratio 3 --repetitions 2 --expand-distance 3 --output benchmark_results.txt

    NOTA: cada execução de benchmark tem um tempo limite de 60s. Caso este limite seja excedido, o solver é desativado para testes subsequentes.
