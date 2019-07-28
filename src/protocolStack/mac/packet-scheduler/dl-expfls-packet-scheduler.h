#ifndef DL_EXPFLS_PACKET_SCHEDULER_H_
#define DL_EXPFLS_PACKET_SCHEDULER_H_

#include "downlink-packet-scheduler.h"


class DL_FLSEXP_PacketScheduler : public DownlinkPacketScheduler {
public:
	DL_FLSEXP_PacketScheduler();
	virtual ~DL_FLSEXP_PacketScheduler();
	virtual void DoSchedule (void);
	virtual void DoStopSchedule (void);
	void RunControlLaw ();
	virtual double ComputeSchedulingMetric (RadioBearer *bearer, double spectralEfficiency, int subChannel);
	double ComputeAverageOfHOLDelays (void);
	virtual void Select_FlowsToSchedule ();
	void UpdateDataToTransmitAndAverageDataRate (void);


private:
	bool m_runControlLaw;
	int m_subFrameCounter;
	int m_startPrbAllocation;
	double m_avgHOLDelayes;
};

#endif /* DL_FLS_PACKET_SCHEDULER_H_ */
