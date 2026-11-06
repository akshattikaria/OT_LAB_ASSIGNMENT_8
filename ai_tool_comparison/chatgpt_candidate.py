def solve_knapsack(weights,values,capacity):
    def integer(x):return isinstance(x,int) and not isinstance(x,bool)
    if not isinstance(weights,(list,tuple)) or not isinstance(values,(list,tuple)):raise ValueError('Expected lists/tuples')
    if len(weights)!=len(values) or not integer(capacity) or capacity<0:raise ValueError('Invalid capacity/lengths')
    if any(not integer(w) or w<=0 for w in weights):raise ValueError('Invalid weights')
    if any(not integer(v) or v<0 for v in values):raise ValueError('Invalid values')
    dp=[None]*(capacity+1);dp[0]=(0,())
    for i,(w,v) in enumerate(zip(weights,values)):
        for used in range(capacity,w-1,-1):
            before=dp[used-w]
            if before is None:continue
            candidate=(before[0]+v,before[1]+(i,));current=dp[used]
            if current is None or candidate[0]>current[0] or (candidate[0]==current[0] and candidate[1]<current[1]):dp[used]=candidate
    options=[(entry[0],w,entry[1]) for w,entry in enumerate(dp) if entry is not None]
    v,w,indices=min(options,key=lambda r:(-r[0],r[1],r[2]));return {'value':v,'weight':w,'indices':list(indices)}
