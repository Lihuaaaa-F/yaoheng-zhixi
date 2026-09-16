WITH scenario_wide(产品, 场景月份, 单位成本, 环比, 同比, 预算差异, 跨厂差异, 主要贡献, 主要贡献率) AS (
  VALUES
    ('银黄口服液','2026-05',11.21,2.844,4.669,5.755,-3.362,'直接材料',70.97),
    ('板蓝根颗粒','2026-05',7.47,3.177,5.211,6.714,-6.274,'直接材料',78.26),
    ('六味地黄胶囊','2026-03',17.02,-3.295,0.591,-0.468,-6.381,'三项均下降',NULL)
), comparison AS (
  SELECT 产品,'环比' AS 比较基准,环比 AS 差异率,场景月份,单位成本,主要贡献,主要贡献率 FROM scenario_wide
  UNION ALL SELECT 产品,'同比',同比,场景月份,单位成本,主要贡献,主要贡献率 FROM scenario_wide
  UNION ALL SELECT 产品,'预算差异',预算差异,场景月份,单位成本,主要贡献,主要贡献率 FROM scenario_wide
  UNION ALL SELECT 产品,'跨厂差异',跨厂差异,场景月份,单位成本,主要贡献,主要贡献率 FROM scenario_wide
)
SELECT 产品,比较基准,差异率,场景月份,单位成本,主要贡献,主要贡献率 FROM comparison
ORDER BY CASE 产品 WHEN '银黄口服液' THEN 1 WHEN '板蓝根颗粒' THEN 2 ELSE 3 END,
         CASE 比较基准 WHEN '环比' THEN 1 WHEN '同比' THEN 2 WHEN '预算差异' THEN 3 ELSE 4 END;

