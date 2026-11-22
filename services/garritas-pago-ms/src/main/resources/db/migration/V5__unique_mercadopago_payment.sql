CREATE UNIQUE INDEX uk_pago_payment_id ON pagos (payment_id) WHERE payment_id IS NOT NULL;
