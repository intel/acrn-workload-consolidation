import json
import base64
import os
import time
import paho.mqtt.client as mqtt


class MqttClient():
    """
    This is a Mosquitto Client class that will create an interface to connect to mosquitto
    by creating mqtt clients.

    It provides methods for connecting, diconnecting, publishing, subscribing, unsubscribing and 
    also callbacks related to many different events like on_connect, on_message, on_publish, on_subscribe,
    on_unsubcribe, on_disconnect.

    """
    def __init__(self, name='user', clientid=None, clean_session=True, userdata=None, pub_only=False, sub_only=False, host='localhost', port=1883, keepalive=60, bind_address=''):
        """
        Create a new instance of the MosquittoClient class, passing in the client
        informaation, host, port, keepalive parameters.

        :param  name:               name of client trying to connect to msoquitto 
        :type   name:               string
        :param  clientid:           unique client id for a client-broker connection
        :type   clientid:           string
        :param  clean_session:      whether to keep persistant connecion or not
        :type   clean_session:      bool
        :param  userdata:           user defined data of any type that is passed as the userdata parameter to callbacks.
                                    It may be updated at a later point with the user_data_set() function.
        :type   userdata:           user defined data (can be int, string, or any object)
        :param  host:               the hostname or IP address of the remote broker
        :type   host:               string
        :param  port:               the network port of the server host to connect to. Defaults to 1883.
                                    Note that the default port for MQTT over SSL/TLS is 8883 so if you are using tls_set() the port may need providing manually
        :type   port:               int
        :param  keepalive:          maximum period in seconds allowed between communications with the broker. 
                                    If no other messages are being exchanged, this controls the rate at which the client will send ping messages to the broker
        :type   keepalive:          int 
        :param  bind_address:       the IP address of a local network interface to bind this client to, assuming multiple interfaces exist
        :type   bind_address:       string

        """
        # pi('__init__')
        self._name = name
        self._clientid = clientid or self._genid() 
        self._clean_session = clean_session 
        self._userdata = userdata 
        self._host = host 
        self._port = port 
        self._keepalive = keepalive 
        self._bind_address = bind_address 
        self._pub_only = pub_only
        self._sub_only = sub_only

        
        self._connected = False
        self._connecting = False
        self._closing = False
        self._closed = False
        self._connection = None
        self._client = None
        # pr('__init__')

    def _genid(self):
        """ 
        Method that generates unique clientids by calling base64.urlsafe_b64encode(os.urandom(32)).replace('=', 'e').
        
        :return:        Returns a unique urlsafe id 
        :rtype:         string 

        """ 

        # pi('_genid')

        return str(base64.urlsafe_b64encode(os.urandom(32)).replace(b'=', b'e'))

    def start(self):
        """
        Method to start the mosquitto client by initiating a connection  to mosquitto broker
        by using the connect method and staring the network loop.

        """

        # pi('start')

        print('[MosquittoClient] starting the mosquitto connection')

        self.setup_connection()
        self.setup_callbacks()
        
        # self._connection is the return code of the connection, success, failure, error. Success = 0
        self._connection = self.connect()

        # print '[MosquittoClient] self._connection : ', self._connection

        if self._connection == 0:
            # Start paho-mqtt mosquitto Event/IO Loop
            print('[MosquittoClient] Startig Loop for client : %s ' % self)            
            self._client.loop_start()
        else:
            self._connecting = False 
            print('[MosquittoClient] Connection for client :  %s  with broker Not Established ' % self)

        # pr('start')
    
    def setup_connection(self):
        """
        Method to setup the extra options like username,password, will set, tls_set etc 
        before starting the connection.

        """ 

        # pi('setup_connection')

        self._client = self.create_client()
        # pr('setup_connection')
    
    def create_client(self):
        """
        Method to create the paho-mqtt Client object which will be used to connect 
        to mosquitto. 
        
        :return:        Returns a mosquitto mqtt client object 
        :rtype:         paho.mqtt.client.Client 

        """ 

        # pi('create_client')

        return mqtt.Client(client_id=self._clientid, clean_session=self._clean_session, userdata=self._userdata)

    def setup_callbacks(self):
        """
        Method to setup all callbacks related to the connection, like on_connect,
        on_disconnect, on_publish, on_subscribe, on_unsubcribe etc. 

        """ 

        # pi('setup_callbacks')

        self._client.on_connect = self.on_connect 
        self._client.on_disconnect = self.on_disconnect 
        if self._pub_only:
            self._client.on_publish = self.on_publish 
        elif self._sub_only:
            self._client.on_subscribe = self.on_subscribe 
            self._client.on_unsubcribe = self.on_unsubscribe
        else:
            self._client.on_publish = self.on_publish
            self._client.on_subscribe = self.on_subscribe
            self._client.on_unsubcribe = self.on_unsubscribe
        # pr('setup_callbacks')

    def connect(self):
        """
        This method connects to Mosquitto via returning the 
        connection return code.

        When the connection is established, the on_connect callback
        will be invoked by paho-mqtt.

        :return:        Returns a mosquitto mqtt connection return code, success, failure, error, etc 
        :rtype:         int

        """

        # pi('connect')

        if self._connecting:
            print('[MosquittoClient] Already connecting to Mosquitto')
            return

        self._connecting = True

        if self._connected: 
            print('[MosquittoClient] Already connected to Mosquitto')

        else:
            print('[MosquittoClient] Connecting to Mosquitto on {}:{}, Object: {} '.format(self._host, self._port, self))

            # pr('connect')

            return self._client.connect(host=self._host, port=self._port, keepalive=self._keepalive, bind_address=self._bind_address)

    def on_connect(self, client, userdata, flags, rc): 
        """
        This is a Callback method and is called when the broker responds to our
        connection request. 

        :param      client:     the client instance for this callback 
        :param      userdata:   the private user data as set in Client() or userdata_set() 
        :param      flags:      response flags sent by the broker 
        :type       flags:      dict
        :param      rc:         the connection result 
        :type       rc:         int

        flags is a dict that contains response flags from the broker:

        flags['session present'] - this flag is useful for clients that are using clean session
        set to 0 only. If a client with clean session=0, that reconnects to a broker that it has
        previously connected to, this flag indicates whether the broker still has the session 
        information for the client. If 1, the session still exists. 

        The value of rc indicates success or not:

        0: Connection successful 1: Connection refused - incorrect protocol version 
        2: Connection refused - invalid client identifier 3: Connection refused - server unavailable 
        4: Connection refused - bad username or password 5: Connection refused - not authorised 
        6-255: Currently unused.

        """ 

        # pi('on_connect')

        if self._connection == 0:
            self._connected = True

            print('[MosquittoClient] Connection for client :  %s  with broker established, Return Code : %s ' % (client, str(rc)))

        else:
            self._connecting = False 
            print('[MosquittoClient] Connection for client :  %s  with broker Not Established, Return Code : %s ' % (client, str(rc)))


        # pr('on_connect')

    def disconnect(self):   
        """
        Method to disconnect the mqqt connection with mosquitto broker.

        on_disconnect callback is called as a result of this method call. 

        """ 

        # pi('disconnect')

        if self._closing: 
            print('[MosquittoClient] Connection for client :  %s  already disconnecting..' % self)

        else:
            self._closing = True 

            if self._closed:
                print('[MosquittoClient] Connection for client :  %s  already disconnected ' % self)

            else:
                self._client.disconnect() 
        # pr('disconnect')

    def on_disconnect(self, client, userdata, rc):
        """
        This is a Callback method and is called when the client disconnects from
        the broker.

        """  

        # pi('on_disconnect')

        print('[MosquittoClient] Connection for client :  %s  with broker cleanly disconnected with return code : %s ' % (client, str(rc)))

        self._connecting = False 
        self._connected = False 
        self._closing = True
        self._closed = True
        self._client.loop_stop() 
        # pr('on_disconnect')

    def subscribe(self, topic=None, on_message=None):
        """
        This method sets up the mqtt client to start subscribing to topics by accepting a list of tuples
        of topic and qos pairs.

        The on_subscribe method is called as a callback if subscribing is succesfull or if it unsuccessfull, the broker
        returng the suback frame. 

        :param      :topic:    topic. 
        :type       :topic:    string 

        """
        # pi('subscribe')
        print('[MosquittoClient] client : %s started Subscribing ' % self)
        self._client.subscribe(topic)
        self._client.on_message = on_message
       
        # pr('subscribe')

    def on_subscribe(self, client, userdata, mid, granted_qos): 
        """
        This is a Callback method and is called when the broker responds to a subscribe request.

        The mid variable matches the mid variable returned from the corresponding subscribe() call.
        The granted_qos variable is a list of integers that give the QoS level the broker has granted
        for each of the different subscription requests. 

        :param      client:         the client which subscribed which triggered this callback 
        :param      userdata:       the userdata associated with the client during its creation 
        :param      mid:            the message id value returned by the broker 
        :type       mid:            int 
        :param      granted_qos:    list of integers that give the QoS level the broker has granted 
                                    for each of the different subscription requests 
        :type       granted_qos:    list

        """

        # pi('on_subscribe')

        print('[MosquittoClient] client :  %s  subscribed to topic succesfully with message id : %s ' % (client, str(mid)))
        # pr('on_subscribe')

    def unsubscribe(self, topic_list=None):
        """
        This method sets up the mqtt client to unsubscribe to topics by accepting topics as string or list.

        The on_unsubscribe method is called as a callback if unsubscribing is succesfull or if it unsuccessfull. 

        :param      topic:        The topic to be unsubscribed from 
        :type       topic:        string

        """
        # pi('unsubscribe')
        print('[MosquittoClient] clinet : %s started Unsubscribing ' % self)
        self._client.unsubscribe(topic)
        # pr('unsubscribe')
    
    def on_unsubscribe(self, client, userdata, mid): 
        """
        This is a Callback method and is called when the broker responds to an 
        unsubscribe request. The mid variable matches the mid variable returned from t
        he corresponding unsubscribe() call. 

        :param      client:             the client which initiated unsubscribed
        :param      userdata:           the userdata associated with the client 
        :param      mid:                the message id value sent by the broker of the unsubscribe call. 
        :type       mid:                int 

        """

        # pi('on_unsubscribe')

        print('[MosquittoClient] client :  %s  unsubscribed to topic succesfully with message id : %s ' % (client, str(mid)))

        # pr('on_unsubscribe')

    def publish(self, topic, msg=None, qos=2, retain=False):
        """
        If the class is not stopping, publish a message to MosquittoClient.

        on_publish callback is called after broker confirms the published message.
        
        :param  topic:  The topic the message is to published to
        :type   topic:  string 
        :param  msg:    Message to be published to broker
        :type   msg:    string 
        :param  qos:    the qos of publishing message 
        :type   qos:    int (0, 1 or 2) 
        :param  retain: Should the message be retained or not 
        :type   retain: bool

        """
        # LOGGER.info('[MosquittoClient] Publishing message')

        # converting message to json, to pass the message(dict) in acceptable format (string)
        if isinstance(msg, str):
            payload = msg
        else:
            payload = json.dumps(msg, ensure_ascii=False)

        self._client.publish(topic=topic, payload=payload, qos=qos, retain=retain)


    def on_publish(self, client, userdata, mid): 
        """
        This is a Callback method and is called when a message that was to be sent
        using the publish() call has completed transmission to the broker. For messages
        with QoS levels 1 and 2, this means that the appropriate handshakes have completed.

        For QoS 0, this simply means that the message has left the client. 
        The mid variable matches the mid variable returned from the corresponding publish()
        call, to allow outgoing messages to be tracked.

        This callback is important because even if the publish() call returns success,
        it does not always mean that the message has been sent.

        :param      client:         the client who initiated the publish method 
        :param      userdata:       the userdata associated with the client during its creation 
        :param      mid:            the message id sent by the broker 
        :type       mid:            int 

        """
        pass
        # pi('on_publish')

        # print('[MosquittoClient] client :  %s  published message succesfully with message id : %s ' % (client, str(mid)))

        # pr('on_publish')

    def stop(self):
        """
        Cleanly shutdown the connection to Mosquitto by disconnecting the mqtt client.

        When mosquitto confirms disconection, on_disconnect callback will be called.

        """

        # pi('stop')

        print('[MosquittoClient] Stopping MosquittoClient object... : %s ' % self)

        self.disconnect()

        # pr('stop')


