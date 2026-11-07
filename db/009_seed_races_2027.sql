-- Triatlón Rianxo · Carreiras de nov. 2026 a out. 2027 (sen ninguén apuntado)
-- As 'previstas' levan '(data prevista)' no nome: a data é a habitual, hai que confirmala.
-- Pódese executar varias veces: non duplica carreiras co mesmo nome e data.
SET NAMES utf8mb4;

INSERT INTO races (name, race_date, start_time, place, zone, sport, distances, official_url, price, created_by)
SELECT v.name, v.race_date, NULL, v.place, v.zone, v.sport, v.distances, v.official_url, NULL, NULL FROM (
  SELECT 'Maratona do Porto' AS name, DATE '2026-11-08' AS race_date, 'Porto' AS place, 'portugal' AS zone, 'running' AS sport, 'Maratona' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Maratón de Málaga' AS name, DATE '2026-11-08' AS race_date, 'Málaga' AS place, 'spain' AS zone, 'running' AS sport, 'Maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Nada e Corre – Ribeira' AS name, DATE '2026-11-08' AS race_date, 'Ribeira' AS place, 'galicia' AS zone, 'other' AS sport, 'Swimrun menores' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Nada e Corre – A Coruña' AS name, DATE '2026-11-14' AS race_date, 'A Coruña' AS place, 'galicia' AS zone, 'other' AS sport, 'Swimrun menores' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Nada e Corre – Cariño' AS name, DATE '2026-11-14' AS race_date, 'Cariño' AS place, 'galicia' AS zone, 'other' AS sport, 'Swimrun menores' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Nada e Corre – Muros' AS name, DATE '2026-11-14' AS race_date, 'Muros' AS place, 'galicia' AS zone, 'other' AS sport, 'Swimrun menores' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'XII Barbanza Arousa + Q Tapas' AS name, DATE '2026-11-20' AS race_date, 'A Pobra do Caramiñal' AS place, 'galicia' AS zone, 'running' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Maratón de Donostia' AS name, DATE '2026-11-22' AS race_date, 'Donostia' AS place, 'spain' AS zone, 'running' AS sport, 'Maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Nada e Corre – Lugo' AS name, DATE '2026-11-28' AS race_date, 'Lugo' AS place, 'galicia' AS zone, 'other' AS sport, 'Swimrun menores' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Nada e Corre – Ourense' AS name, DATE '2026-11-28' AS race_date, 'Ourense' AS place, 'galicia' AS zone, 'other' AS sport, 'Swimrun menores' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Maratón Valencia' AS name, DATE '2026-12-06' AS race_date, 'Valencia' AS place, 'spain' AS zone, 'running' AS sport, 'Maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'XXI Carreira Popular Mar de Boiro – Memorial Pepe Buceta' AS name, DATE '2026-12-06' AS race_date, 'Boiro' AS place, 'galicia' AS zone, 'running' AS sport, '10 km, 2,5 km, 200 m' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Nada e Corre – Final' AS name, DATE '2026-12-13' AS race_date, 'Ribeira' AS place, 'galicia' AS zone, 'other' AS sport, 'Swimrun menores' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'San Silvestre da Coruña (data prevista)' AS name, DATE '2026-12-31' AS race_date, 'A Coruña' AS place, 'galicia' AS zone, 'running' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'San Silvestre de Vigo (data prevista)' AS name, DATE '2026-12-31' AS race_date, 'Vigo' AS place, 'galicia' AS zone, 'running' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'XVIII Dúatlon de Reis' AS name, DATE '2027-01-10' AS race_date, 'Vimianzo' AS place, 'galicia' AS zone, 'duathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Media Maratón de Granollers' AS name, DATE '2027-01-24' AS race_date, 'Granollers' AS place, 'spain' AS zone, 'running' AS sport, 'Media maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'CXM A Camelia (data prevista)' AS name, DATE '2027-02-07' AS race_date, 'Galicia' AS place, 'galicia' AS zone, 'trail' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Maratón de Murcia' AS name, DATE '2027-02-07' AS race_date, 'Murcia' AS place, 'spain' AS zone, 'running' AS sport, 'Maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Cto. España de Dúatlon MD' AS name, DATE '2027-02-14' AS race_date, 'Almazán (Soria)' AS place, 'spain' AS zone, 'duathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Dúatlon Vilalba CRE' AS name, DATE '2027-02-14' AS race_date, 'Vilalba' AS place, 'galicia' AS zone, 'duathlon' AS sport, 'Contrarreloxo por equipos' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Marató BP Castelló' AS name, DATE '2027-02-14' AS race_date, 'Castelló' AS place, 'spain' AS zone, 'running' AS sport, 'Maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Mitja Marató de Barcelona' AS name, DATE '2027-02-14' AS race_date, 'Barcelona' AS place, 'spain' AS zone, 'running' AS sport, 'Media maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'V Dúatlon Val de Soneira' AS name, DATE '2027-02-20' AS race_date, 'Vimianzo' AS place, 'galicia' AS zone, 'duathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'I Dúatlon Ferrecal Compostela' AS name, DATE '2027-02-21' AS race_date, 'Santiago de Compostela' AS place, 'galicia' AS zone, 'duathlon' AS sport, 'Menores' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Zurich Maratón de Sevilla' AS name, DATE '2027-02-21' AS race_date, 'Sevilla' AS place, 'spain' AS zone, 'running' AS sport, 'Maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Transgrancanaria (data prevista)' AS name, DATE '2027-02-24' AS race_date, 'Gran Canaria' AS place, 'spain' AS zone, 'trail' AS sport, '128 km, 82 km, 42 km' AS distances, 'https://transgrancanaria.net/' AS official_url
  UNION ALL
  SELECT 'Dúatlon Vedra CRE' AS name, DATE '2027-03-06' AS race_date, 'Vedra' AS place, 'galicia' AS zone, 'duathlon' AS sport, 'Contrarreloxo por equipos' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Dúatlon clasificatorio Cto. España' AS name, DATE '2027-03-07' AS race_date, 'Ólvega (Soria)' AS place, 'spain' AS zone, 'duathlon' AS sport, 'Sprint' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Medio Maratón de Málaga' AS name, DATE '2027-03-07' AS race_date, 'Málaga' AS place, 'spain' AS zone, 'running' AS sport, 'Media maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Meia Maratona de Lisboa' AS name, DATE '2027-03-07' AS race_date, 'Lisboa' AS place, 'portugal' AS zone, 'running' AS sport, 'Meia maratona' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Zurich Marató de Barcelona' AS name, DATE '2027-03-14' AS race_date, 'Barcelona' AS place, 'spain' AS zone, 'running' AS sport, 'Maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Desafío Oia (data prevista)' AS name, DATE '2027-03-21' AS race_date, 'Oia' AS place, 'galicia' AS zone, 'trail' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Dúatlon Avilés (calendario nacional FETRI)' AS name, DATE '2027-04-03' AS race_date, 'Avilés (Asturias)' AS place, 'spain' AS zone, 'duathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Medio Maratón Gran Bahía Vig-Bay (data prevista)' AS name, DATE '2027-04-04' AS race_date, 'Vigo – Baiona' AS place, 'galicia' AS zone, 'running' AS sport, '21,1 km, 10,5 km' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Medio Maratón de Madrid' AS name, DATE '2027-04-04' AS race_date, 'Madrid' AS place, 'spain' AS zone, 'running' AS sport, 'Media maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'XXIV Dúatlon Cidade de Santiago' AS name, DATE '2027-04-10' AS race_date, 'Santiago de Compostela' AS place, 'galicia' AS zone, 'duathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Challenge Mogán Gran Canaria (data prevista)' AS name, DATE '2027-04-17' AS race_date, 'Mogán (Gran Canaria)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Dúatlon Eleuterio Balayo' AS name, DATE '2027-04-17' AS race_date, 'Muros' AS place, 'galicia' AS zone, 'duathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Dúatlon de Zuia (ZuiaDu)' AS name, DATE '2027-04-17' AS race_date, 'Murgia, Zuia (Álava)' AS place, 'spain' AS zone, 'duathlon' AS sport, 'Media distancia: 15 km + 70 km + 7 km' AS distances, 'https://zuiadu.com/' AS official_url
  UNION ALL
  SELECT 'IRONMAN 70.3 Valencia' AS name, DATE '2027-04-18' AS race_date, 'Valencia' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia (70.3)' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'MIUT – Madeira Island Ultra-Trail' AS name, DATE '2027-04-24' AS race_date, 'Madeira' AS place, 'portugal' AS zone, 'trail' AS sport, '115 km, 85 km, 60 km, 42 km, 16 km' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'CXM Montes de Viveiro (CAMOVI) (data prevista)' AS name, DATE '2027-04-25' AS race_date, 'Viveiro' AS place, 'galicia' AS zone, 'trail' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Maratona da Europa' AS name, DATE '2027-04-25' AS race_date, 'Aveiro' AS place, 'portugal' AS zone, 'running' AS sport, 'Maratona, Meia maratona' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Rock ''n'' Roll Madrid Maratón' AS name, DATE '2027-04-25' AS race_date, 'Madrid' AS place, 'spain' AS zone, 'running' AS sport, 'Maratón, Media maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Oh Meu Deus Ultra Trail' AS name, DATE '2027-04-30' AS race_date, 'Seia (Serra da Estrela)' AS place, 'portugal' AS zone, 'trail' AS sport, '166 km, 90 km, 50 km, 26 km' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Trail Orixes de Mondariz (data prevista)' AS name, DATE '2027-05-01' AS race_date, 'Mondariz' AS place, 'galicia' AS zone, 'trail' AS sport, 'Ultra' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'IRONMAN 70.3 Alcúdia-Mallorca' AS name, DATE '2027-05-08' AS race_date, 'Alcúdia (Mallorca)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia (70.3)' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Segura Extreme' AS name, DATE '2027-05-08' AS race_date, 'Segura de la Sierra (Jaén)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Longa distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Triatlón Cross Calahorra (FETRI)' AS name, DATE '2027-05-08' AS race_date, 'Calahorra (La Rioja)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Cross' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Triatlón de Oleiros (data prevista)' AS name, DATE '2027-05-08' AS race_date, 'Oleiros' AS place, 'galicia' AS zone, 'triathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Challenge Salou (data prevista)' AS name, DATE '2027-05-09' AS race_date, 'Salou (Tarragona)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Tríatlon do Porriño' AS name, DATE '2027-05-09' AS race_date, 'O Porriño' AS place, 'galicia' AS zone, 'triathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'IRONMAN Lanzarote' AS name, DATE '2027-05-15' AS race_date, 'Puerto del Carmen (Lanzarote)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Longa distancia (Ironman)' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Trail Serra do Barbanza (data prevista)' AS name, DATE '2027-05-16' AS race_date, 'Miradoiro da Curotiña (A Pobra)' AS place, 'galicia' AS zone, 'trail' AS sport, '26 km, 15 km, 7 km' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Zegama-Aizkorri Maratoia (data prevista)' AS name, DATE '2027-05-16' AS race_date, 'Zegama (Gipuzkoa)' AS place, 'spain' AS zone, 'trail' AS sport, '42 km' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Tri100 Llanes (data prevista)' AS name, DATE '2027-05-23' AS race_date, 'Llanes (Asturias)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Serra Amarela Sky Marathon (data prevista)' AS name, DATE '2027-05-30' AS race_date, 'Entre Ambos-os-Rios (Ponte da Barca)' AS place, 'portugal' AS zone, 'trail' AS sport, '48 km, 33 km, 23 km, 15 km' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Campionato de Europa de Dúatlon' AS name, DATE '2027-06-05' AS race_date, 'Cáceres' AS place, 'spain' AS zone, 'duathlon' AS sport, 'Estándar' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Triatlón Mar de Muros' AS name, DATE '2027-06-05' AS race_date, 'Muros' AS place, 'galicia' AS zone, 'triathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'GPM A Rúa (data prevista)' AS name, DATE '2027-06-06' AS race_date, 'A Rúa' AS place, 'galicia' AS zone, 'trail' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Gran Maratón Montañas de Benasque' AS name, DATE '2027-06-12' AS race_date, 'Benasque (Huesca)' AS place, 'spain' AS zone, 'trail' AS sport, '42 km' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Triatlón clasificatorio Cto. España' AS name, DATE '2027-06-12' AS race_date, 'Aguilar de Campoo (Palencia)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Olímpico' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'II Triatlón Lagoa das Pontes' AS name, DATE '2027-06-20' AS race_date, 'As Pontes' AS place, 'galicia' AS zone, 'triathlon' AS sport, 'Olímpico, Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Triatlón Gravel Vinuesa' AS name, DATE '2027-06-20' AS race_date, 'Vinuesa (Soria)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Gravel' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Cto. España de Triatlón cadete, xuvenil e júnior' AS name, DATE '2027-06-26' AS race_date, 'Pontevedra' AS place, 'galicia' AS zone, 'triathlon' AS sport, 'Sprint' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Val d''Aran by UTMB' AS name, DATE '2027-07-07' AS race_date, 'Vielha (Lleida)' AS place, 'spain' AS zone, 'trail' AS sport, '163 km, 110 km, 75 km, 55 km, 30 km, 18 km, 10 km' AS distances, 'https://valdaran.utmb.world/' AS official_url
  UNION ALL
  SELECT 'Triatlón Cidade da Coruña (data prevista)' AS name, DATE '2027-07-10' AS race_date, 'A Coruña' AS place, 'galicia' AS zone, 'triathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'IRONMAN 70.3 Vitoria-Gasteiz' AS name, DATE '2027-07-11' AS race_date, 'Vitoria-Gasteiz' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia (70.3)' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'IRONMAN Vitoria-Gasteiz' AS name, DATE '2027-07-11' AS race_date, 'Vitoria-Gasteiz' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Longa distancia (Ironman)' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Acuatlón de menores de Narón' AS name, DATE '2027-07-16' AS race_date, 'Narón' AS place, 'galicia' AS zone, 'aquathlon' AS sport, 'Menores' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Triatlón de Ferrol (data prevista)' AS name, DATE '2027-07-17' AS race_date, 'Ferrol' AS place, 'galicia' AS zone, 'triathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Trishark Narón' AS name, DATE '2027-07-17' AS race_date, 'Narón' AS place, 'galicia' AS zone, 'triathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Travesía a Nado Ría de Vigo (data prevista)' AS name, DATE '2027-08-01' AS race_date, 'Vigo' AS place, 'galicia' AS zone, 'open_water' AS sport, '1 km, 3,7 km' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Travesía a Nado do Porto de Vilagarcía (data prevista)' AS name, DATE '2027-08-01' AS race_date, 'Vilagarcía de Arousa' AS place, 'galicia' AS zone, 'open_water' AS sport, '2.500 m, 1.200 m, 250 m' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Travesía Vila do Tea (data prevista)' AS name, DATE '2027-08-07' AS race_date, 'Ponteareas' AS place, 'galicia' AS zone, 'open_water' AS sport, '3.600 m' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Travesía a Nado do Lérez (data prevista)' AS name, DATE '2027-08-08' AS race_date, 'Pontevedra' AS place, 'galicia' AS zone, 'open_water' AS sport, '4.000 m' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Triatlón do Miño' AS name, DATE '2027-08-08' AS race_date, 'Lugo' AS place, 'galicia' AS zone, 'triathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Descenso a Nado de Salvaterra de Miño (data prevista)' AS name, DATE '2027-08-21' AS race_date, 'Salvaterra de Miño' AS place, 'galicia' AS zone, 'open_water' AS sport, '4 km, 2,5 km, 1 km' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'EMEDE Valladolid (data prevista)' AS name, DATE '2027-08-21' AS race_date, 'Valladolid' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Travesía a Nado Illa da Bensa (data prevista)' AS name, DATE '2027-08-21' AS race_date, 'Boiro' AS place, 'galicia' AS zone, 'open_water' AS sport, '3.500 m, 1.000 m, 200 m' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'XXXV Triatlón Vila de Allariz' AS name, DATE '2027-08-21' AS race_date, 'Allariz' AS place, 'galicia' AS zone, 'triathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Triatlón de Zarautz (data prevista)' AS name, DATE '2027-08-22' AS race_date, 'Zarautz (Gipuzkoa)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'XVIII Carreira Popular Concello da Pobra (data prevista)' AS name, DATE '2027-08-29' AS race_date, 'A Pobra do Caramiñal' AS place, 'galicia' AS zone, 'running' AS sport, '8 km' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Half de Ribadeo (data prevista)' AS name, DATE '2027-09-04' AS race_date, 'Ribadeo' AS place, 'galicia' AS zone, 'triathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Ultra Trail Cerveira (data prevista)' AS name, DATE '2027-09-05' AS race_date, 'Vila Nova de Cerveira' AS place, 'portugal' AS zone, 'trail' AS sport, '46 km, 21 km, 15 km' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Acuatlón de Narón (data prevista)' AS name, DATE '2027-09-11' AS race_date, 'Narón' AS place, 'galicia' AS zone, 'aquathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Castelo de Vitres (data prevista)' AS name, DATE '2027-09-11' AS race_date, 'Galicia' AS place, 'galicia' AS zone, 'trail' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Desafío FEGAN 2,5K (final Circuito Galego) (data prevista)' AS name, DATE '2027-09-12' AS race_date, 'Praia de Coroso, Ribeira' AS place, 'galicia' AS zone, 'open_water' AS sport, '2.500 m, 1.250 m, 500 m' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Meia Maratona do Porto (data prevista)' AS name, DATE '2027-09-12' AS race_date, 'Porto' AS place, 'portugal' AS zone, 'running' AS sport, 'Meia maratona' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'T100 Marbella – Cto. España MD' AS name, DATE '2027-09-19' AS race_date, 'Marbella (Málaga)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia (T100)' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Triatlón de Santander (data prevista)' AS name, DATE '2027-09-19' AS race_date, 'Santander' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Triatlón Banyoles (internacional)' AS name, DATE '2027-09-25' AS race_date, 'Banyoles (Girona)' AS place, 'spain' AS zone, 'triathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Media Maratón de Valladolid' AS name, DATE '2027-09-26' AS race_date, 'Valladolid' AS place, 'spain' AS zone, 'running' AS sport, 'Media maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Acuatlón Copa Deputación de Ourense (data prevista)' AS name, DATE '2027-10-02' AS race_date, 'Castrelo de Miño' AS place, 'galicia' AS zone, 'aquathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Half Madrid' AS name, DATE '2027-10-03' AS race_date, 'Madrid' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'IRONMAN Calella-Barcelona' AS name, DATE '2027-10-03' AS race_date, 'Calella (Barcelona)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Longa distancia (Ironman)' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Medio Maratón de Donostia' AS name, DATE '2027-10-03' AS race_date, 'Donostia' AS place, 'spain' AS zone, 'running' AS sport, 'Media maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Triatlón de Cadavedo (data prevista)' AS name, DATE '2027-10-03' AS race_date, 'Cadavedo (Asturias)' AS place, 'spain' AS zone, 'triathlon' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'EDP Maratona de Lisboa' AS name, DATE '2027-10-09' AS race_date, 'Cascais – Lisboa' AS place, 'portugal' AS zone, 'running' AS sport, 'Maratona, Meia maratona' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Challenge Peguera Mallorca (data prevista)' AS name, DATE '2027-10-16' AS race_date, 'Peguera (Mallorca)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Cto. España LD – Desafío Doñana' AS name, DATE '2027-10-16' AS race_date, 'Matalascañas (Huelva)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Longa distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'ICAN Gandia Full' AS name, DATE '2027-10-16' AS race_date, 'Gandia (Valencia)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Longa distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'ICAN Gandia Half' AS name, DATE '2027-10-16' AS race_date, 'Gandia (Valencia)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Canón do Sil (data prevista)' AS name, DATE '2027-10-17' AS race_date, 'Ribeira Sacra' AS place, 'galicia' AS zone, 'trail' AS sport, NULL AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Palma de Mallorca Marathon (data prevista)' AS name, DATE '2027-10-17' AS race_date, 'Palma' AS place, 'spain' AS zone, 'running' AS sport, 'Maratón, Media maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Challenge Barcelona (data prevista)' AS name, DATE '2027-10-23' AS race_date, 'Calella (Barcelona)' AS place, 'spain' AS zone, 'triathlon' AS sport, 'Media distancia' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'Medio Maratón Valencia' AS name, DATE '2027-10-24' AS race_date, 'Valencia' AS place, 'spain' AS zone, 'running' AS sport, 'Media maratón' AS distances, NULL AS official_url
  UNION ALL
  SELECT 'XIII Carreira Popular Concello de Rianxo (data prevista)' AS name, DATE '2027-10-30' AS race_date, 'Rianxo' AS place, 'galicia' AS zone, 'running' AS sport, '10 km, 6,6 km' AS distances, NULL AS official_url
) AS v
WHERE NOT EXISTS (SELECT 1 FROM races r WHERE r.name = v.name AND r.race_date = v.race_date);
