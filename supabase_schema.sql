-- Savol javob — Supabase'da bir marta ishga tushiriladigan sozlash skripti.
-- Supabase loyihangizda: SQL Editor -> New query -> shu faylni to'liq joylashtirib "Run" bosing.

create table if not exists yonalishlar (
  id bigint generated always as identity primary key,
  name text unique not null
);

create table if not exists savollar (
  id bigint generated always as identity primary key,
  yonalish_id bigint references yonalishlar(id) on delete cascade,
  text text not null,
  answer text default '',
  created_at timestamptz default now()
);

create table if not exists natijalar (
  id bigint generated always as identity primary key,
  filial text,
  ism text,
  familya text,
  tugilgan text,
  manzil text,
  yonalish text,
  jami_ball numeric,
  max_ball numeric,
  ortacha_ball numeric,
  yechilgan integer,
  savollar_soni integer,
  tafsilot jsonb,
  hakamlar jsonb,
  yaratilgan_vaqt timestamptz default now()
);

-- Xavfsizlik: bu jadvallarga faqat dasturning o'zi (service_role kaliti orqali) yoza oladi.
-- service_role RLS'ni chetlab o'tadi, shuning uchun policy qo'shishning hojati yo'q.
alter table yonalishlar enable row level security;
alter table savollar enable row level security;
alter table natijalar enable row level security;
