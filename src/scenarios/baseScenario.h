#include "../channel/LteChannel.h"
#include "../core/spectrum/bandwidth-manager.h"
#include "../networkTopology/Cell.h"
#include "../core/eventScheduler/simulator.h"
#include "../flows/application/InfiniteBuffer.h"
#include "../flows/QoS/QoSParameters.h"
#include "../componentManagers/FrameManager.h"
#include "../componentManagers/FlowsManager.h"

static void baseScenario(){
    Simulator *simulator = Simulator::Init();
    FrameManager *frameManager = FrameManager::Init();
    NetworkManager *networkManager = NetworkManager::Init();
    FlowsManager *flowManager = FlowsManager::Init();

    //Channels and Spectrum
    LteChannel *dlChannel = new LteChannel();
    LteChannel *ulChannel = new LteChannel();
    BandwidthManager *spectrum = new BandwidthManager(5, 5, 0, 0);

    //LTE CELL
    int idCell = 0;
    int radius = 5; //km
    int minDistance = .0035; //km
    pair<int, int> position = make_pair(0, 0);
    Cell *cell = networkManager->CreateCell(idCell, radius, minDistance, position.first, position.second);

    //Create ENB
    int idEnB = 1;
    ENodeB *enb = networkManager->CreateEnodeb(idEnB, cell, position.first, position.second, dlChannel, ulChannel, spectrum);
    enb->SetDLScheduler(ENodeB::DLScheduler_TYPE_PROPORTIONAL_FAIR);

    //Create GW
    Gateway *gw = networkManager->CreateGateway();

    //Create UE
    int idUE = 2;
    pair<int, int> positionUE = make_pair(40, 0);
    int speed = 3;//km/h
    double speedDirection = 0;
    UserEquipment *ue = networkManager->CreateUserEquipment(idUE, positionUE.first, positionUE.second, speed, speedDirection, cell, enb);

    //Create App
    QoSParameters *qos = new QoSParameters();
    qos->SetMaxDelay(.1);
    int appID = 0;
    int srcPort = 0;
    int dstPort = 100;
    int startTime = 10;
    int stopTime = 30;
    int size = 5;
    double interval = 0.04;
    Application *app = flowManager->CreateApplication(appID, gw, ue, srcPort, dstPort, TransportProtocol::TRANSPORT_PROTOCOL_TYPE_UDP, Application::APPLICATION_TYPE_CBR, qos, startTime, stopTime);
    ((CBR*) app)->SetSize(size);
    ((CBR*) app)->SetInterval(interval);
    // CBR_Rate = (size*8/interval) * 0.001   kbps.

    simulator->SetStop(60);
    simulator->Run();
}