# meshroom create integration

!!! Usage
    **meshroom create integration** [OPTIONS] PRODUCT TARGET_PRODUCT TOPIC
                                   *{consumer|producer|trigger|executor}*

  Scaffold a new Integration with the given role (consumer, producer, trigger or executor).
  A consumer is the complementary integration of a producer.
  An executor is the complementary integration of a trigger.

  An integration always consume/produce or trigger/execute one given **topic**, in a predefined mode (**push** or **pull**)

  If the PRODUCT declares a `@scaffold` hook, it will be called to generate the integration's boilerplate.

### Options

option | description
--- | ---
  --mode [push\|pull] | Set the operation mode of the integration. Push means the producer is active and the consumer is passive, while Pull means the producer is passive and the consumer is active
  -f, --format TEXT | Set the data format supported by this integration. Only integrations with identical format or format-agnostic one will match this integration
