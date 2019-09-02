set -x
set -e

_COUNT=1
_NB_SEEDS=5

until [ $_COUNT -gt $_NB_SEEDS ]; do
for sched in 1 2 3 4 5 6 7 8 #scheduling algorithm
do
for ue in 10 20 30 40 50 #number of users
do
	../../LTE-Sim SingleCell 1 $ue 0 0 .5 .5 $sched $v .04 .06 .08 .1 242 > TRACE/SCHED_${sched}_UE_${ue}_$_COUNT
	cd TRACE
	gzip SCHED_${sched}_UE_${ue}_V_${v}_D_${del}_$_COUNT
	cd ..
done
done
_COUNT=$(($_COUNT + 1))
done
