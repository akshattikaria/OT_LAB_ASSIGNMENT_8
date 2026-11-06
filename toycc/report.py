"""Report own measured results; embed all scientific plots for offline reading."""
import base64
from html import escape
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .experiment import VARIANTS


def build_report(directory):
    root=Path(directory);figures=root/'figures';figures.mkdir(exist_ok=True);read=lambda n:json.loads((root/n).read_text())
    compile_rows=read('compile_runs.json');runtime=read('runtime_runs.json');search=read('pass_search.json');stats=read('native_function_stats.json');builds=read('native_builds.json');protocol=read('protocol.json');validation=read('validation.json');env=read('environment.json')
    first={(r['program'],r['variant']):r for r in compile_rows if r['repeat']==0};families=protocol['families'];ids=sorted(set(r['program'] for r in compile_rows));med=lambda x:float(np.median(x))
    short=['Base','Fold','CSE','DCE','Strength','Fixed','Greedy','DP'];colors=['#777','#2479a5','#7a61a9','#b07c47','#9a5c73','#559a65','#d88a36','#087f8c']
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,'figure.dpi':125,'axes.titleweight':'bold'})
    files=[]
    def save(fig,name):fig.tight_layout();fig.savefig(figures/name,bbox_inches='tight');plt.close(fig);files.append(name)
    def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)
    def graphic(name,caption):return f'![{caption}](figures/{name})\n\n{caption}'
    summaries=[];per_program=[]
    for name in ids:
        base=first[name,'baseline'];family=base['family'];row={'program':name,'family':family,'baseline_ir':base['ir_instructions'],'dp_ir':first[name,'dp_order']['ir_instructions'],
            'baseline_score':base['weighted_ir_score'],'dp_score':first[name,'dp_order']['weighted_ir_score'],'greedy_score':first[name,'greedy_order']['weighted_ir_score'],'fixed_score':first[name,'fixed']['weighted_ir_score']}
        for level in ('O0','O2'):
            times={method:med([r['seconds'] for r in runtime if r['program']==name and r['variant']==method and r['level']==level]) for method in ('baseline','dp_order')}
            row[level+'_speedup']=times['baseline']/times['dp_order'];row[level+'_baseline_s']=times['baseline'];row[level+'_dp_s']=times['dp_order']
        per_program.append(row)
    for family in families:
        rows=[r for r in per_program if r['family']==family];names=[r['program'] for r in rows]
        summary={'family':family,'programs':len(rows),'mean_ir_reduction':float(np.mean([1-r['dp_ir']/r['baseline_ir'] for r in rows])),
            'mean_source_reduction':float(np.mean([1-first[name,'dp_order']['function_source_bytes']/first[name,'baseline']['function_source_bytes'] for name in names]))}
        for level in ('O0','O2'):
            summary[level+'_mean_speedup']=float(np.mean([r[level+'_speedup'] for r in rows]));summary[level+'_min_speedup']=min(r[level+'_speedup'] for r in rows);summary[level+'_max_speedup']=max(r[level+'_speedup'] for r in rows)
            for key in ('machine_code_bytes','static_disassembly_instructions'):
                fractions=[]
                for name in names:
                    baseline=next(r[key] for r in stats if r['program']==name and r['level']==level and r['variant']=='baseline');optimized=next(r[key] for r in stats if r['program']==name and r['level']==level and r['variant']=='dp_order');fractions.append(optimized/baseline)
                summary[level+'_'+key+'_ratio']=float(np.mean(fractions))
        summaries.append(summary)
    fig,axes=plt.subplots(1,2,figsize=(12,4.5));matrix=np.array([[np.mean([first[name,method]['ir_instructions']/first[name,'baseline']['ir_instructions'] for name in ids if first[name,'baseline']['family']==family]) for method in VARIANTS] for family in families])
    axes[0].imshow(matrix,cmap='YlGnBu',vmin=0,vmax=max(1,float(matrix.max())),aspect='auto');axes[0].set_xticks(range(8),short,rotation=30,ha='right');axes[0].set_yticks(range(4),[x.replace('_',' ') for x in families]);axes[0].grid(False);axes[0].set_title('Mean retained IR body instructions')
    for y in range(4):
        for x in range(8):axes[0].text(x,y,f'{matrix[y,x]:.0%}',ha='center',va='center',color='white' if matrix[y,x]>.6 else '#16343d',fontsize=9)
    axes[1].bar(range(4),[s['mean_ir_reduction']*100 for s in summaries],color='#087f8c');axes[1].set_xticks(range(4),[x.replace('_','\n') for x in families]);axes[1].set_ylabel('Mean reduction (%)');axes[1].set_title('DP vs unoptimized IR');save(fig,'ir_changes.png')

    fig,axes=plt.subplots(1,2,figsize=(11,4.2));x=np.arange(len(per_program))
    for method,color in (('greedy','#d88a36'),('fixed','#559a65')):
        excess=[100*(r[method+'_score']/r['dp_score']-1) for r in per_program];axes[0].scatter(x,excess,label=method,color=color,s=27)
    axes[0].axhline(0,color='#555',ls=':');axes[0].set_xlabel('Program index (all retained)');axes[0].set_ylabel('Weighted score above exact best (%)');axes[0].set_title('DP verified against every 24-order oracle');axes[0].legend(fontsize=8)
    for index,key in enumerate(('states','transition_evaluations','cache_hits')):
        axes[1].bar(np.arange(4)+(index-1)*.24,[np.mean([s['dp'][key] for s in search if s['family']==family]) for family in families],width=.24,label=key.replace('_',' '),color=('#087f8c','#d88a36','#7a61a9')[index])
    axes[1].set_xticks(range(4),[f.replace('_','\n') for f in families]);axes[1].set_ylabel('Mean count');axes[1].set_title('Memoized states include the transformed IR');axes[1].legend(fontsize=8);save(fig,'pass_search.png')

    fig,axes=plt.subplots(1,2,figsize=(11,4.3))
    for ax,level in zip(axes,('O0','O2')):
        for index,family in enumerate(families):
            values=[r[level+'_speedup'] for r in per_program if r['family']==family];ax.bar(index,np.mean(values),color='#087f8c' if level=='O0' else '#d88a36',alpha=.8);ax.scatter(np.full(len(values),index),values,color='#333',s=21)
        ax.axhline(1,color='#444',ls=':');ax.set_xticks(range(4),[f.replace('_','\n') for f in families]);ax.set_ylabel('Baseline median time / DP median time');ax.set_title('Native '+level+' (all program seeds)')
    save(fig,'native_runtime.png')

    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    for ax,key,title in zip(axes,('static_disassembly_instructions','machine_code_bytes'),('Static native instruction ratio','Native function code-byte ratio')):
        for index,level in enumerate(('O0','O2')):ax.bar(np.arange(4)+(index-.5)*.32,[s[level+'_'+key+'_ratio'] for s in summaries],width=.32,label=level,color=('#087f8c','#d88a36')[index])
        ax.axhline(1,color='#555',ls=':');ax.set_xticks(range(4),[f.replace('_','\n') for f in families]);ax.set_ylabel('DP / baseline');ax.set_title(title);ax.legend(fontsize=8)
    save(fig,'code_size.png')

    fig,axes=plt.subplots(1,2,figsize=(11,4.2));compile_summary=[]
    for index,method in enumerate(VARIANTS):
        rows=[r for r in compile_rows if r['variant']==method];milliseconds=1000*med([r['python_compile_s'] for r in rows]);axes[0].bar(index,milliseconds,color=colors[index]);compile_summary.append({'variant':method,'median_python_compile_s':milliseconds/1000,'median_optimization_s':med([r['optimization_s'] for r in rows])})
    axes[0].set_xticks(range(8),short,rotation=30,ha='right');axes[0].set_ylabel('Median milliseconds (log)');axes[0].set_yscale('log');axes[0].set_title('Frontend + pass/search work + C generation')
    for index,level in enumerate(('O0','O2')):axes[1].bar(np.arange(4)+(index-.5)*.32,[1000*med([b['native_compile_s'] for b in builds if b['family']==family and b['optimization']==level]) for family in families],width=.32,label=level,color=('#087f8c','#d88a36')[index])
    axes[1].set_xticks(range(4),[f.replace('_','\n') for f in families]);axes[1].set_ylabel('Median C-compiler milliseconds');axes[1].set_title('Combined eight-variant translation unit');axes[1].legend();save(fig,'compile_cost.png')

    fig,ax=plt.subplots(figsize=(10,4.2));ablation=[]
    for index,method in enumerate(VARIANTS):
        ratios=[]
        for name in ids:
            base=med([r['seconds'] for r in runtime if r['program']==name and r['variant']=='baseline' and r['level']=='O0']);other=med([r['seconds'] for r in runtime if r['program']==name and r['variant']==method and r['level']=='O0']);ratios.append(base/other)
        ax.bar(index,np.mean(ratios),color=colors[index]);ax.scatter(np.full(len(ratios),index),ratios,color='#333',s=9,alpha=.4);ablation.append({'variant':method,'mean_O0_speedup':float(np.mean(ratios)),'min_O0_speedup':min(ratios),'max_O0_speedup':max(ratios)})
    ax.axhline(1,ls=':',color='#555');ax.set_xticks(range(8),short);ax.set_ylabel('Within-program native O0 speedup');ax.set_title('Single-pass ablations and complete pass orders');save(fig,'ablation.png')

    sections=[]
    def add(title,body):sections.append((title,body))
    add('Track F: Compiler Optimization','Prepared for Akshat Tikaria, roll number 241070005. Assignment 8.\n\nThis package implements a complete small arithmetic compiler: an explicit lexer, precedence parser, immutable three-address SSA, four optimization passes, a register interpreter and C code generation. It compares the same programs with eight compiler variants and two native host-compiler levels. All reported runtime and code-size numbers are measured from the retained artifacts. This is a toy-language study, not a production C compiler or an LLVM/GCC plugin.')
    add('Protocol and measurements',table(['Evidence','Recorded work'],[
        ['Programs',f'{len(ids)} synthetic programs: four families × {len(protocol["seeds"])} seeds'],
        ['Compiler variants',', '.join(VARIANTS)],['Python compilation',f'{len(compile_rows)} measured compilations; {protocol["compile_repeats"]} repeats/variant/program'],
        ['Native runtime',f'{len(runtime)} timings; {protocol["runtime_repeats"]} repeats; {protocol["iterations_per_timing"]:,} calls/timing'],
        ['Native builds',f'{len(builds)} real shared-library builds, at O0/O2'],['Function metrics',f'{len(stats)} native symbol/disassembly records'],
        ['Pass-order references',f'{24*len(ids)} complete four-pass permutations'],['Equivalence',f'{sum(v["ir_comparisons"] for v in validation):,} IR and {sum(v["native_comparisons"] for v in validation):,} native input/output comparisons']])+'\nNative compiler: '+env['compiler_version']+'. Python: '+env['python'].splitlines()[0]+'. Runs are serial CPU measurements on a shared cloud workspace; no student-laptop, GPU, dedicated-core or parallel speedup claim is made.\n\nEvery native timing uses the same varying-input LCG driver, checksum, iteration count and seed within a comparison. Trial order is predeclared and shuffled. Medians use all timing repeats; figures aggregate the within-program median ratios across generated programs. Dots show every program seed, not selected best runs. Native function boundaries are kept with noinline; the driver and indirect call overhead remain in all timings.')
    add('Language and correctness assumptions','Functions have immutable let bindings and one return; at most eight uint64 arguments. Supported expressions are +, −, *, bitwise XOR/AND/OR and left/right shifts. Every arithmetic result wraps modulo 2^64; shift counts are masked to 0–63. Right shift is logical unsigned. There are no branches, source loops, mutable stores, pointers, I/O, division or exceptions. These restrictions make each expression pure and total, which is essential for dead-code removal and common-expression reuse.\n\n```\nfn demo(x,y,z) {\n    let dead = x * y;\n    let k = 2 * 4;\n    let a = x + y;\n    let b = y + x;\n    return a * k + b * 8 + 0;\n}\n```\n\nThe parser enforces definition-before-use, immutable names, literal bounds, argument count and syntax. The native backend uses unsigned C11 arithmetic and explicitly masks shift counts. It does not depend on undefined signed overflow or unsafe floating-point reassociation. AST, IR and generated native C are compared on zero, boundary, high-bit, wraparound and random inputs; a separate AST loop verifies the native benchmark checksum.')
    add('Four implemented passes',table(['Pass','Transformation','Condition'],[
        ['Fold/propagate','Compute constant expressions; propagate aliases/constants; valid uint64 identities','Preserve modulo arithmetic and masked shifts'],
        ['CSE','Reuse identical SSA expressions; canonicalize commutative operands','Immutable definitions and pure operations'],
        ['DCE','Backward liveness from the returned result','Unused operations have no side effects or traps'],
        ['Strength reduction','Multiply by 2^k becomes left shift by k','Unsigned wrap semantics; k in 0–63']])+'\n'+graphic('ir_changes.png','All eight variants are retained. An IR body count includes argument loads and constants but excludes the final return and benchmark driver; in this straight-line language each retained IR instruction executes once per invocation.')+'\nFold/propagate is counted as one combined pass; there are four separately implemented transformations. Strength reduction can temporarily add a shift-count constant while leaving the old constant dead, so a later DCE/CSE pass can matter. No loop optimization or register allocation is claimed.\n\n'+table(['Family','Mean IR count reduction','Mean generated C-function byte reduction'],[[s['family'],f'{s["mean_ir_reduction"]:.2%}',f'{s["mean_source_reduction"]:.2%}'] for s in summaries]))
    better=sum(r['dp_score']<r['greedy_score'] for r in per_program)
    add('Compiler decision as dynamic programming','Decision variables choose an ordering of the four passes, each used exactly once. The objective is final weighted IR cost: multiplication=4; every other retained instruction=1. These are fixed teaching-model weights, not measured CPU cycles. The constraint is a permutation of the four supported passes.\n\nState is (used-pass bit mask, canonical transformed IR). A transition applies an unused pass; the terminal value is the final IR score. The recurrence takes the minimum terminal score over all legal next passes, with memoization and a deterministic tie break. Keeping only the subset would be wrong because different orders can leave different IR for the same subset. Canonical renumbering merges structurally equal SSA states.\n\nThe fixed baseline is fold→CSE→strength→DCE. Greedy selects the pass with the best immediate score; DP looks through the remaining interactions. An independent enumeration of all 24 permutations checks each finite optimum. The certificate covers this score and search space; it is neither global compiler optimality nor native-runtime optimality.\n\n'+graphic('pass_search.png','DP matches every exhaustive oracle; memoization shares identical transformed states rather than assuming all pass orders commute.')+f'\nDP obtained a strictly lower score than greedy on {better}/{len(ids)} programs. Four passes make exact verification practical; search-state growth can become expensive with a larger pass set. The report retains search work and compilation cost alongside final code quality.')
    add('Measured native runtime',graphic('native_runtime.png','Bars are arithmetic means of within-program median-time ratios. Each dot is one generated program; the two panels use separate vertical scales.')+'\n'+table(['Family','Mean O0 speedup','O0 program range','Mean O2 speedup','O2 program range'],[[s['family'],f'{s["O0_mean_speedup"]:.3f}',f'{s["O0_min_speedup"]:.3f}–{s["O0_max_speedup"]:.3f}',f'{s["O2_mean_speedup"]:.3f}',f'{s["O2_min_speedup"]:.3f}–{s["O2_max_speedup"]:.3f}'] for s in summaries])+'\nThe O0 comparison isolates pedagogical pass effects with most host optimization disabled. It must not be presented as outperforming an optimizing production compiler. At O2, the host compiler already removes many redundancies, so additional gains are small, inconsistent or negative. Code shape, alignment, kernel overhead and timing variability also matter; a lower synthetic IR score need not imply lower native runtime. No statistical-significance claim is made from a few short shared-host measurements.\n\n'+graphic('ablation.png','Single-pass variants show that one transformation can help a family, have little effect, or add overhead. Only baseline and DP are timed at O2; all eight variants are timed at O0.'))
    add('Instruction counts and code size',graphic('code_size.png','Native instruction counts come from saved objdump disassembly; function code bytes come from nm symbol sizes. These are static quantities, not retired CPU instruction counts.')+'\nFunction source bytes are measured on the generated function text. Native symbol bytes exclude the shared benchmark driver and most shared-library metadata. Each library contains all eight variants, so total library file size is recorded as build information and is not misrepresented as one variant’s executable size. Disassembly counts may include compiler-inserted alignment/padding. At O2, some cases converge while others grow; this exposes a mismatch between the teaching cost model and the native target. In the mixed family, DP averaged about 2.45 times the baseline function bytes and a 0.889 runtime ratio (baseline time / DP time). Raw source, IR, C, assembly and symbol metrics are retained for inspection.')
    add('Compile-time trade-off',graphic('compile_cost.png','Python time includes a fresh lex/parse/lower, optimization/search and function generation for each variant. C compiler time belongs to the combined eight-variant translation unit.')+'\n'+table(['Variant','Median Python compile ms','Median optimization/search ms'],[[r['variant'],f'{1000*r["median_python_compile_s"]:.4f}',f'{1000*r["median_optimization_s"]:.4f}'] for r in compile_summary])+'\nGreedy considers ten candidate transitions. DP explores more states and caches repeated states, increasing compilation work to obtain the exact finite score optimum. Runtime gains amortize compilation cost only if generated code runs enough times. Native compilation is measured separately and is not divided arbitrarily among variants. All stage timings are retained, so one can distinguish source transformation from the external host compiler.')
    add('Validation, AI revision and limits','All 29 unit tests pass, including 6,000 random-program/all-order differential cases, overflow and masked shifts, every power-of-two strength rewrite, independent AST/IR evaluation, and native O0/O2 comparisons. The saved-data audit checks inputs, compiled outputs, C regeneration, disassembly counts, all 24-order certificates and same-seed runtime checksums, and freshly recompiles C under both levels. Its exact counts are in audit.json.\n\nA genuine AI-generated search-work defect was caught before the recorded benchmarks: greedy transformed every candidate twice, but reported ten transitions. Instrumentation observed twenty transformation calls. Reusing each computed candidate fixed the waste and accounting; the original/fix commits, observation and regression are retained. Earlier A/B/D packages already contain three other corrected cases. No manual student correction or independent second-tool comparison is claimed.\n\nThis is a small, pure straight-line language and four-pass cost-model study. Differential checks are finite evidence; pass-soundness arguments rely on the declared pure/total unsigned semantics. No branch/loop correctness proof, production workload generalization, LLVM plugin, universal performance ranking or hardware-cycle optimum is claimed. Next is Track G (xv6), followed by H/I/J and final integration; outstanding research-paper reproductions, full chat exports, second-tool comparison, public repository and demonstration remain open.')
    add('Primary references','- Supplied Assignment 8, Track F, and Chapter 6 discrete/strategy-selection material. Lecture files are acknowledged rather than redistributed.\n- LLVM transform-pass reference: https://llvm.org/docs/Passes.html (conceptual reference; no LLVM dependency).\n- GCC optimization levels: https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html\n- GCC function attributes: https://gcc.gnu.org/onlinedocs/gcc/Common-Function-Attributes.html\n- Public references checked 2026-11-04. All experiment numbers come from the retained local runs; the toy language’s unsigned semantics and score are explicitly defined here.')
    markdown='\n\n'.join('# '+title+'\n\n'+body for title,body in sections)+'\n';(root/'REPORT.md').write_text(markdown,encoding='utf-8')
    def render(body):
        lines=body.splitlines();out=[];i=0
        while i<len(lines):
            line=lines[i]
            if line=='```':
                code=[];i+=1
                while i<len(lines) and lines[i]!='```':code.append(lines[i]);i+=1
                out.append('<pre><code>'+escape('\n'.join(code))+'</code></pre>');i+=1;continue
            if line.startswith('| '):
                rows=[]
                while i<len(lines) and lines[i].startswith('| '):rows.append([s.strip() for s in lines[i].strip('|').split('|')]);i+=1
                out.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+escape(v)+'</th>' for v in rows[0])+'</tr></thead><tbody>')
                for row in rows[2:]:out.append('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in row)+'</tr>')
                out.append('</tbody></table></div>');continue
            if line.startswith('!['):
                name=line.split('(figures/',1)[1].rstrip(')');data=base64.b64encode((figures/name).read_bytes()).decode();out.append('<img alt="'+escape(line[2:line.index(']')])+'" src="data:image/png;base64,'+data+'">')
            elif line:out.append('<p>'+escape(line)+'</p>')
            i+=1
        return '\n'.join(out)
    html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Track F Compiler Optimization</title><style>body{margin:0;background:#eef3f5;color:#1b3640;font:16px/1.6 system-ui,sans-serif}main{max-width:1160px;margin:32px auto;padding:36px;background:white;border-top:8px solid #087f8c;border-radius:12px}h1{font-size:32px;line-height:1.2}h2{font-size:24px;color:#075e69;margin-top:42px}img{width:100%;height:auto;margin:18px 0}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:10px;border-bottom:1px solid #dbe6e9}th{background:#e8f3f3}p{overflow-wrap:anywhere}pre{padding:20px;background:#eef4f6;overflow-x:auto;font-size:14px;line-height:1.5}@media(max-width:700px){main{margin:0;padding:20px}}</style><main>'
    for i,(title,body) in enumerate(sections):tag='h1' if i==0 else 'h2';html+='<'+tag+'>'+escape(title)+'</'+tag+'>'+render(body)
    (root/'report.html').write_text(html+'</main></html>',encoding='utf-8');(root/'summary.json').write_text(json.dumps({'families':summaries,'per_program':per_program,'python_compile':compile_summary,'ablation':ablation,'dp_strictly_better_than_greedy':better},indent=2)+'\n');return files
