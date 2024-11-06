



# Heating simulation
## Simulation
adapted from https://github.com/timtroendle/simple-simple

### Equation
$\Theta_{Z_i,t+1}=\Theta_{Z_i,t} - \text{(temperature energy lost to surrounding)} + \text{(temperature energy gained)}$

$\Theta_{Z_i,t+1}=\Theta_{Z_i,t} - \frac{\Delta t}{C_{Z_1}}\Theta_{Z_i,t}(H_{tr,eZ_1}+\sum_{Z_j\in Z_{n}(Z_i)} H_{tr,Z_iZ_j}) + \frac{\Delta t}{C_{Z_i}}(\Phi_{H,Z_i,t-1}+H_{tr,eZ_i}\Theta_{e,t} + \sum H_{tr,Z_iZ_j} \Theta_{Z_j,t})$

with
- $\Theta_{Z_i,t}$: Temperature in $\text{Zone }i$ at time step $t$, $[°C]$
- $\Delta t$: duration of time step, $[s]$
- $C_{Z_i}$: temperature capacity of $\text{Zone }i$, $[W/°C]$, $i\in\{1,2,3\}$
- $H_{tr,eZ_i}$: heat transmission coeficient from environment ($e$) to $\text{Zone }i$, $[W/°C]$
- $Z_n(Z_i)$: neighbouring zones to $\text{Zone }i$
- $\Phi_{H,Z_i,t-1}$: heating power, $[W]$

### Constants
- $\Theta_{Z_i,t=0}=\Theta_{e}=10\,°C$
- $\Delta t=1\,s$
- $C_{Z_1}=C_{Z_2}=C_{Z_3}=3\times 10^6\,\frac J{°C}$
- $H_{tr,eZ_1}=H_{tr,eZ_3}=500\,\frac W{°C}$
- $H_{tr,eZ_2}=400\,\frac W{°C}$
- $H_{tr,Z_1Z_2}=H_{tr,Z_2Z_3}=1000\,\frac W{°C}$
- $Z_n(Z_1)=\{ Z_2\}$
- $Z_n(Z_2)=\{ Z_1,Z_3\}$
- $Z_n(Z_3)=\{ Z_2\}$
- $\Phi_{H}= 10\,kW$ if turned on, else $\Phi_{H}= 0\,W$

## Simulation inputs
for each time step:
- which heater is switched on?
- $\Theta_{e,t=n}, \Theta_{Z_1,t=n}, \Theta_{Z_2,t=n}, \Theta_{Z_3,t=n}$

## Simulation outputs
for each time step:
- $\Theta_{Z_1,t=n+1}, \Theta_{Z_2,t=n+1}, \Theta_{Z_3,t=n+1}$
 
## Notes
The objective temperature for the heating controller is $t=22°C$.

