#ifndef DL_EXPFLS_PACKET_SCHEDULER_H_
#define DL_EXPFLS_PACKET_SCHEDULER_H_

#include "downlink-packet-scheduler.h"
#include "../mac-entity.h"
#include "../../packet/Packet.h"
#include "../../packet/packet-burst.h"
#include "../../../device/NetworkNode.h"
#include "../../../flows/radio-bearer.h"
#include "../../../protocolStack/rrc/rrc-entity.h"
#include "../../../flows/application/Application.h"
#include "../../../device/ENodeB.h"
#include "../../../protocolStack/mac/AMCModule.h"
#include "../../../phy/lte-phy.h"
#include "../../../core/spectrum/bandwidth-manager.h"
#include "../../../flows/QoS/QoSForFLS.h"
#include "../../../flows/MacQueue.h"
#include "../../../utility/eesm-effective-sinr.h"


class DL_FLSEXP_PacketScheduler : public DownlinkPacketScheduler {
public:
	DL_FLSEXP_PacketScheduler(ENodeB::DLSchedulerType scheduler);
	virtual ~DL_FLSEXP_PacketScheduler();

	virtual void DoSchedule (void);
	virtual void DoStopSchedule (void);
	virtual double ComputeSchedulingMetric (RadioBearer *bearer, double spectralEfficiency, int subChannel);


private:
	bool m_runControlLaw;
	int m_subFrameCounter;
	double m_avgHOLDelayes;
	ENodeB::DLSchedulerType internalMetric;
	double pfMetric(RadioBearer *bearer, double spectralEfficiency);
	double logRuleMetric(RadioBearer *bearer, double spectralEfficiency);
	double expRuleMetric(RadioBearer *bearer, double spectralEfficiency, int subChannel, double m_avgHOLDelayes);
	double ComputeAverageOfHOLDelays (void);
	void RunControlLaw ();
	void Select_FlowsToSchedule ();
	void UpdateDataToTransmitAndAverageDataRate (void);


};

#endif /* DL_FLS_PACKET_SCHEDULER_H_ */
