#include "EbFtClient.hh"

#include "Endpoint.hh"

#include <rdma/fi_rma.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>                     // For sleep()...

using namespace Pds;
using namespace Pds::Fabrics;
using namespace Pds::Eb;

static const size_t scratch_size = sizeof(Fabrics::RemoteAddress);


EbFtClient::EbFtClient(StringList&  remote,
                       std::string& port,
                       size_t       lclSize,
                       size_t       rmtSize) :
  EbFtBase(remote.size()),
  _remote(remote),
  _port(port),
  _lclSize(lclSize),
  _rmtSize(rmtSize),
  _base(new char[lclSize])
{
}

EbFtClient::~EbFtClient()
{
  delete[] _base;
}

int EbFtClient::connect(unsigned tmo)
{
  if (_base == NULL)
  {
    fprintf(stderr, "No memory available for a region of size %zd\n", _lclSize);
    return -1;
  }

  for (unsigned i = 0; i < _remote.size(); ++i)
  {
    int ret = _connect(_remote[i], _port, tmo, _ep[i], _mr[i]);
    if (ret)
    {
      fprintf(stderr, "_connect() failed at index %u\n", i);
      return ret;
    }

    printf("Client %d connected\n", i);

    // Borrow the local region for a moment to obtain the remote region specs
    ret = _syncRmtMr(_base, _rmtSize, _ep[i], _mr[i], _ra[i]);
    if (ret)  return ret;

    ret = _syncLclMr(_base, _lclSize, _ep[i], _mr[i]);
    if (ret)  return ret;
  }

  return 0;
}

int EbFtClient::_connect(std::string&   remote,
                         std::string&   port,
                         unsigned       tmo,
                         Endpoint*&     ep,
                         MemoryRegion*& mr)
{
  ep = new Endpoint(remote.c_str(), port.c_str());
  if (!ep || (ep->state() != EP_UP))
  {
    fprintf(stderr, "Failed to initialize fabrics endpoint %s:%s: %s\n",
            remote.c_str(), port.c_str(), ep->error());
    perror("new Endpoint");
    return ep ? ep->error_num() : -1;
  }

  Fabric* fab = ep->fabric();

  mr = fab->register_memory(_base, _lclSize);
  if (!mr)
  {
    fprintf(stderr, "Failed to register memory region @ %p, sz %zu: %s\n",
            _base, _lclSize, fab->error());
    perror("fab->register_memory");
    return fab->error_num();
  }

  bool tmoEnabled = tmo != 0;
  while (!ep->connect() && (!tmoEnabled || --tmo))
  {
    sleep (1);
  }
  if (tmoEnabled && (tmo == 0))
  {
    fprintf(stderr, "Failed to connect endpoint %s:%s: %s\n",
            remote.c_str(), port.c_str(), ep->error());
    perror("ep->connect()");
    return -1;
  }

  return 0;
}

int EbFtClient::shutdown()
{
  int ret = FI_SUCCESS;

  //for (unsigned i = 0; i < _ep.size(); ++i)
  //{
  //  // Revisit: What's needed here?
  //}

  return ret;
}