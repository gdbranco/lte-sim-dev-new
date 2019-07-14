set -x
set -e

_COUNT=1
_NB_SEEDS=3

until [ $_COUNT -gt $_NB_SEEDS ]; do
for sched in 1 2 3 4 5 6 #scheduling algorithm
do
for ue in 10 20 30 40 50 #number of users
do
for del in 0.1 	#target delay
do	
for v in 3			#users speed
do
	../../LTE-Sim SingleCell 1 $ue .25 .25 .25 .25 $sched $v $del 242 > TRACE/SCHED_${sched}_UE_${ue}_V_${v}_D_${del}_$_COUNT
	cd TRACE
	gzip SCHED_${sched}_UE_${ue}_V_${v}_D_${del}_$_COUNT
	cd ..
done
done
done
done
_COUNT=$(($_COUNT + 1))
done
