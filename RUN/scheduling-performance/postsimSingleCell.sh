set -x
set -e

TOOLS="../../TOOLS"
time=100

_NB_SCREENSHOT=10
_COUNT=1
until [ $_COUNT -gt $_NB_SCREENSHOT ]; do
for sched in  1 2 3 4 5 6          #scheduling algorithm
do
for ue in 10 20 30 40 50        #number of users
do
for del in 0.1   #target delay
do
for v in 30                  #users speed
do

	FILEIN="SCHED_${sched}_UE_${ue}_V_${v}_D_${del}_$_COUNT"
	PLRVIDEO="OUT/PLRVIDEO_SCHED_${sched}_UE_${ue}_V_${v}_D_${del}"
	PLRVOIP="OUT/PLRVOIP_SCHED_${sched}_UE_${ue}_V_${v}_D_${del}"
	DELVIDEO="OUT/DELVIDEO_SCHED_${sched}_UE_${ue}_V_${v}_D_${del}"
	DELVOIP="OUT/DELVOIP_SCHED_${sched}_UE_${ue}_V_${v}_D_${del}"
	TPUTVIDEO="OUT/TPUTVIDEO_SCHED_${sched}_UE_${ue}_V_${v}_D_${del}"
	TPUTVOIP="OUT/TPUTVOIP_SCHED_${sched}_UE_${ue}_V_${v}_D_${del}"
	TPUTBE="OUT/TPUTBE_SCHED_${sched}_UE_${ue}_V_${v}_D_${del}"
	
	cd TRACE
	unp ${FILEIN}.gz; 
	cd ..

		grep -c "TX VIDEO" TRACE/${FILEIN} > tmp_plr_video
		grep -c "RX VIDEO" TRACE/${FILEIN} >> tmp_plr_video
		${TOOLS}/make_plr tmp_plr_video | awk '{print $2}' | tail -1 >> ${PLRVIDEO}
                                                        
		grep "RX VIDEO" TRACE/${FILEIN} | awk '{print $14}' > tmp_delay_video
		${TOOLS}/make_avg tmp_delay_video >> ${DELVIDEO}

		grep "RX VIDEO" TRACE/${FILEIN} |awk '{print $8}' >> tmp_gput_video
		${TOOLS}/make_goodput tmp_gput_video $time >> ${TPUTVIDEO}
                                                       
		rm TRACE/${FILEIN} 
		rm tmp*
done
done
done
done
_COUNT=$(($_COUNT + 1))

done
