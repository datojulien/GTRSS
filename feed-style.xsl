<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html>
<head>
  <meta charset="UTF-8"/>
  <title><xsl:value-of select="/rss/channel/title"/></title>
  <style>
    body {
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #111;
      color: #f5f5f5;
      line-height: 1.5;
    }

    .hero {
      padding: 56px 24px;
      background: linear-gradient(135deg, #351057, #7b1fa2, #111);
      border-bottom: 1px solid rgba(255,255,255,0.15);
    }

    .wrap {
      max-width: 950px;
      margin: 0 auto;
    }

    h1 {
      margin: 0 0 12px;
      font-size: 42px;
      letter-spacing: -0.04em;
    }

    .subtitle {
      max-width: 720px;
      font-size: 18px;
      opacity: 0.9;
    }

    .badge {
      display: inline-block;
      margin-bottom: 18px;
      padding: 6px 12px;
      border-radius: 999px;
      background: rgba(255,255,255,0.14);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .content {
      padding: 32px 24px 64px;
    }

    .episode {
      display: grid;
      grid-template-columns: 120px 1fr;
      gap: 20px;
      padding: 22px;
      margin-bottom: 18px;
      border-radius: 24px;
      background: #1b1b1f;
      border: 1px solid rgba(255,255,255,0.08);
      box-shadow: 0 10px 35px rgba(0,0,0,0.25);
    }

    .episode img {
      width: 120px;
      height: 120px;
      object-fit: cover;
      border-radius: 18px;
      background: #333;
    }

    .episode h2 {
      margin: 0 0 8px;
      font-size: 22px;
      line-height: 1.2;
    }

    .episode h2 a {
      color: #fff;
      text-decoration: none;
    }

    .date {
      color: #c9a8ff;
      font-size: 14px;
      margin-bottom: 10px;
    }

    .desc {
      color: #ddd;
      margin-bottom: 14px;
    }

    audio {
      width: 100%;
      margin-top: 8px;
    }

    .rss-note {
      margin-top: 24px;
      padding: 16px 18px;
      border-radius: 16px;
      background: rgba(255,255,255,0.08);
      color: #ddd;
      font-size: 14px;
    }

    @media (max-width: 650px) {
      .episode {
        grid-template-columns: 1fr;
      }

      .episode img {
        width: 100%;
        height: auto;
        max-height: 280px;
      }

      h1 {
        font-size: 32px;
      }
    }
  </style>
</head>

<body>
  <section class="hero">
    <div class="wrap">
      <div class="badge">RSS personnel</div>
      <h1><xsl:value-of select="/rss/channel/title"/></h1>
      <div class="subtitle">
        <xsl:value-of select="/rss/channel/description"/>
      </div>
      <div class="rss-note">
        This is a podcast RSS feed. Copy this URL into a podcast app to subscribe.
      </div>
    </div>
  </section>

  <main class="content">
    <div class="wrap">
      <xsl:for-each select="/rss/channel/item">
        <article class="episode">
          <div>
            <xsl:choose>
              <xsl:when test="itunes:image/@href">
                <img>
                  <xsl:attribute name="src">
                    <xsl:value-of select="itunes:image/@href"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
            </xsl:choose>
          </div>

          <div>
            <h2>
              <a>
                <xsl:attribute name="href">
                  <xsl:value-of select="link"/>
                </xsl:attribute>
                <xsl:value-of select="title"/>
              </a>
            </h2>

            <div class="date">
              <xsl:value-of select="pubDate"/>
            </div>

            <div class="desc">
              <xsl:value-of select="description"/>
            </div>

            <audio controls="controls">
              <source>
                <xsl:attribute name="src">
                  <xsl:value-of select="enclosure/@url"/>
                </xsl:attribute>
                <xsl:attribute name="type">
                  <xsl:value-of select="enclosure/@type"/>
                </xsl:attribute>
              </source>
            </audio>
          </div>
        </article>
      </xsl:for-each>
    </div>
  </main>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
