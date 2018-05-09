\COPY p2k12.accounts FROM 'p2k12_accounts.csv' WITH CSV HEADER
\COPY p2k12.auth FROM 'p2k12_auth.csv' WITH CSV HEADER
\COPY p2k12.members FROM 'p2k12_members.csv' WITH CSV HEADER
\COPY p2k12.checkins FROM 'p2k12_checkins.csv' WITH CSV HEADER
\COPY p2k12.stripe_customer FROM 'p2k12_stripe_customer.csv' WITH CSV HEADER
\COPY p2k12.stripe_payment FROM 'p2k12_stripe_payment.csv' WITH CSV HEADER
