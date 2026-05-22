class WeightedGreedySolver:
     
    '''
    Versao greedy diferente: que em vez de contar so quantos retangulos um guarda vigia,
    dá prioridade aos retangulos que que tem menos opcoes de guarda
    '''
    
    def __init__(self, coverage_matrix, required=None):
        self.A = coverage_matrix
        self.num_vertices = len(coverage_matrix)
        self.num_rectangles = len(coverage_matrix[0])
        
        # required: índices dos retângulos que têm de ser cobertos (None = todos)
        self.required = set(required) if required is not None else set(range(self.num_rectangles))
        
    def solve(self):        
        uncovered = set(self.required)
        guards = []
        degree = {}

        # degree[r] = número de guardas que conseguem vigiar o retângulo r        
        for r in self.required:
            degree[r] = sum(self.A[v][r] for v in range(self.num_vertices))

        # weight[r] = importância do retângulo r            
        weights = {}
        for r in self.required:
            weights[r] = 1.0 / degree[r]
            
        while uncovered:
            best_vertex = None
            best_cover = set()
            best_score = -1.0
            
            for v in range(self.num_vertices):
                current_cover = {r for r in uncovered if self.A[v][r] == 1}
                current_score = sum(weights[r] for r in current_cover)
            
                if current_score > best_score:
                    best_score = current_score
                    best_cover = current_cover
                    best_vertex = v

            if best_vertex is None: break
            guards.append(best_vertex)
            uncovered -= best_cover
        
        
        return guards