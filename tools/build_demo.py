"""Captioned guided demo from real CLI output and retained project results."""
import json
from pathlib import Path
import subprocess
import textwrap
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent/'tmp/integration-demo-scenes'
FONTS=Path('/usr/share/fonts/truetype/dejavu')
def font(size,bold=False,mono=False):return ImageFont.truetype(str(FONTS/('DejaVuSansMono.ttf' if mono else 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')),size)
def frame(index,title,lines,duration,graphic=None):
    im=Image.new('RGB',(1920,1080),'#f0f5f8');d=ImageDraw.Draw(im);d.rectangle((0,0,1920,24),fill='#247b8a');d.text((100,70),'ASSIGNMENT 8  |  AKSHAT TIKARIA  |  241070005',font=font(25,True),fill='#4a667c')
    y=150
    for line in textwrap.wrap(title,57):d.text((100,y),line,font=font(49,True),fill='#163e62');y+=67
    y+=25
    for line in lines:
        for part in textwrap.wrap(line,83) or ['']:
            d.text((100,y),part,font=font(31,mono=part.startswith(('baseline','greedy','ilp'))),fill='#273d51');y+=47
        y+=13
    if graphic:
        picture=Image.open(ROOT/graphic).convert('RGB');picture.thumbnail((1700,420));im.paste(picture,((1920-picture.width)//2,1050-picture.height-65))
    d.text((100,1015),'Captioned guide: actual CLI output and retained evidence; synthetic EV data.',font=font(22),fill='#60778c')
    d.text((1730,1015),str(index)+'/6',font=font(22),fill='#60778c');path=WORK/f'scene_{index}.png';im.save(path);return path,duration
def main():
    WORK.mkdir(parents=True,exist_ok=True)
    cli=(ROOT/'validation/ev_demo_output.txt').read_text().strip().splitlines();assert len(cli)==3 and '406.00' in cli[0] and '182.00' in cli[1] and '182.00' in cli[2]
    scenes=[]
    scenes.append(frame(1,'Optimize EV charging without undercharging',[
        'An EV has an arrival, departure, fixed charging rate and energy requirement.',
        'Charging immediately may buy expensive electricity or block an urgent EV.',
        'We compare arrival-priority baseline, deadline/price greedy and joint binary ILP.',
        'This is a scheduling experiment with synthetic sessions and fictional prices.'],14))
    scenes.append(frame(2,'The model: cost subject to valid service',[
        'x_it = 1 means EV i charges in slot t.',
        'Minimize price x power x slot duration over selected EV-slot pairs.',
        'Every EV receives exactly its required slots, inside its availability window.',
        'At every slot, total charging power stays within the station limit.',
        'A cheaper but undercharged schedule is infeasible.'],16))
    scenes.append(frame(3,'Actual four-vehicle command output',[
        'Command: cd tracks/E; python -m evcharge demo','',*cli,'',
        'All three schedules pass independent feasibility checks.',
        'Greedy ties ILP in this small example; other cases expose greedy failures.'],18))
    scenes.append(frame(4,'The main benchmark: 75 synthetic cases',[
        'Main feasibility: baseline 64/75, greedy 70/75, ILP 75/75.',
        'Flexible-window cost reduction: 49.44% across 15 certified matched pairs.',
        'Flat-price cases save 0%. Five main ILP cases have feasible timeout candidates.'],18,'reports/figures/ev_synthesis.png'))
    scenes.append(frame(5,'Why an optimized objective can still disappoint',[
        'xv6: allocator spinning falls to zero, but the page workload is 11.95x slower.',
        'Compiler: many O0 gains disappear under O2; mixed-family runtime regresses.',
        'Software tests: ILP chooses 74 of 391 and cuts median wall time 41.5%,',
        'but misses 3 of the 16 faults caught by the full suite.',
        'Line coverage, lower operation counts and lower contention are surrogate metrics.'],18))
    scenes.append(frame(6,'Reproduce, explain and finish the evidence',[
        'Tests: 243 track + 7 supplement + 20 research; comparison 9/9 per tool.',
        'Run: python tools/audit_project.py',
        'Read the report, exact chapter checklist and raw per-track evidence.',
        'ChatGPT/Gemini comparison recorded. Finish chat exports and GitHub publication.',
        'All 22 research topics have experiments/controls; six are mechanism-only.',
        'Practice explaining the formulation and changing a small input without AI.'],16))
    concat=WORK/'scenes.txt';concat.write_text(''.join(f"file '{p}'\nduration {seconds}\n" for p,seconds in scenes)+f"file '{scenes[-1][0]}'\n")
    out=ROOT/'reports/Assignment_8_Captioned_Demo.mp4'
    command=['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-vsync','vfr','-vf','fps=12,format=yuv420p','-c:v','libx264','-preset','veryfast','-crf','24','-movflags','+faststart',str(out)]
    with (ROOT/'validation/video_build.log').open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(out)],text=True));duration=float(probe['format']['duration']);assert 99<=duration<=102
    (ROOT/'validation/video_check.json').write_text(json.dumps({'duration_s':duration,'width':probe['streams'][0]['width'],'height':probe['streams'][0]['height'],'source_cli_verified':True,'audio':'Silent; captions included','scope':'Edited guided demonstration, not a live screen-capture or physical station recording.'},indent=2)+'\n');print(out)
if __name__=='__main__':main()
