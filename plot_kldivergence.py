from kldivergence import *
import numpy as np
import sys
import matplotlib #For changing rcParams
import getopt

colors = ['g','b','r','c','m','y']

#Parse command line options
optlist,args=getopt.getopt(sys.argv[1:],'lprd:')

for o,a in optlist:        
    if o == '-l': #Use very cool Latex fonts
        print 'Using latex for figures'
        matplotlib.rcParams['text.usetex']=True
        matplotlib.rcParams['font.size']=22.0
    elif o == '-p': #Make nice figures for publication
        matplotlib.rcParams['savefig.dpi']=180.
        matplotlib.rcParams['font.size']=17.0
        matplotlib.rcParams['figure.figsize']=(8.0,6.0)
        matplotlib.rcParams['axes.formatter.limits']=[-10,10]
    elif o=='-f': #Make flatter figures (good for raster plots)
        matplotlib.rcParams['figure.figsize']=(8.0,4.8)
    elif o=='-d':
            et.globaldata.directory=a #Use this directory containing results instead of current

from plot_options import *

if len(sys.argv)==1:
    d=et.globaldata.directory
elif len(sys.argv)==2:
    d=et.globaldata.directory=sys.argv[1]

et.globaldata = et.load()
out = et.globaldata.out

#Nruns=1

nsteps = int(t_sim/t_ref)
def r(params):
    return run_GS(params[0],params[1],params[2], n = nsteps)

def c(p):
    return compute_distr_ns(p[0], p[1], p[2], p[3])

def c_gs(p):
    return compute_distr_ns(p[0], p[1], p[2], p[3], T = int(t_sim/t_ref))

def pmplot(ax, x,y,s, **kwparams):
    plot(x,y, **kwparams)
    kwparams['linewidth']=0
    kwparams['alpha']=0.5
    kwparams.pop('marker')
    fill_between(x, np.maximum(y-s,0), y+s, **kwparams)
    return ax

import multiprocessing
pool = multiprocessing.Pool(24)

states_ns, W, b_v, b_h = zip(*out)
states_ns_ = zip(*states_ns)
states_gs_ = pool.map(r, [(W[i], b_v[i], b_h[i]) for i in range(Nruns)])

#Compute KL divergence for neural samplers
res_ns_params = []
res = []
for k in range(len(states_ns_)):
    res_ns_params.append([(states_ns_[k][i], W[i], b_v[i], b_h[i]) for i in range(Nruns) ])
    res.append( pool.map(c, res_ns_params[k]))

#Compute KL divergence for Gibbs sampler
res_gs_params = [(states_gs_[i], W[i], b_v[i], b_h[i]) for i in xrange(Nruns)]
res_exact = [run_exact(W[i], b_v[i], b_h[i]) for i in xrange(Nruns ) ]
res_gs = pool.map(c_gs, res_gs_params)

avg = lambda x: np.mean([x[i][2] for i in range(len(x))],axis=0)
std = lambda x: np.std([x[i][2] for i in range(len(x))],axis=0)

matplotlib.rcParams['figure.subplot.bottom'] = .19
matplotlib.rcParams['figure.subplot.top'] = .94
matplotlib.rcParams['figure.subplot.right'] = .94
matplotlib.rcParams['figure.subplot.left'] = .18
figure(figsize=[4.8,4.8])
ax = axes()

for k in range(len(states_ns_)):
    pmplot(ax, res[k][0][1] ,avg(res[k]) ,std(res[k])/np.sqrt(Nruns-1),
            color=colors[k],
            linestyle='-',
            marker='x',
            label=str(k),
            #label = '$P_{{ {0}, {1} }}$'.format("NS",runs[0])
            )

pmplot(ax, res[0][0][1] ,avg(res_gs),std(res_gs) ,color='k', linestyle='-', marker='x', label = '$P_{{ {0} }}$'.format("Gibbs"))
ax.set_xscale('log')
ax.set_yscale('log')
ax.grid(True)
ylim([.5e-3,1])
xlabel('Time [s]')
ylabel('Relative Inaccuracy')
legend(loc=3, prop={'size':20}, frameon=True, labelspacing=0.)
draw()
et.savefig('sampling_progress.png')


distr_ns = [res[0][0][0], res[1][0][0]]


##--------------------Plot------------------------------#
f= lambda x: '$[\\mathtt{'+np.binary_repr(x, width=5)+'}]$'
matplotlib.rcParams['figure.subplot.bottom'] = .35
figure(figsize=[10.0,4.8])

Nbars = len(distr_ns)+1
for i,d_ns in enumerate(distr_ns):
    bar(np.arange(32)+0.9*(float(i)+1)/Nbars, -np.log(d_ns[:32]), width=.9/Nbars, linewidth=0, color = colors[i], label = '$P_{{ {0}, {1} }}$'.format("NS",runs[i]))
    xticks(np.array(range(0,32,4)+[31])-1, map(f, range(0,32,4)+[31]), rotation=45)
    xlabel('$\\mathbf{z} = (z_1, z_2, z_3, z_4, z_5)$')
    ylabel('$-log(p(\\mathbf{z}))$')

bar(np.arange(32), -np.log(res_exact[0][:32]), width=.9/Nbars, linewidth=0, color = 'k', label = '$P_{exact}$')
legend(prop={'size':20},labelspacing=0.,frameon=False)

xlim([0,32])
ylim([0,15])
yticks([0,5,10,15])
et.savefig('kldivergence.pdf', format='pdf')

