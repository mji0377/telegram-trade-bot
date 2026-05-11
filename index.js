const { Telegraf, Markup } = require('telegraf')

const bot = new Telegraf(process.env.BOT_TOKEN)

bot.start(async (ctx) => {

  await ctx.replyWithPhoto(
    {
      url: 'https://i.imgur.com/2s9XK4h.jpeg'
    },
    {
      caption: `
🚩 안전 거래 시스템

안전한 거래를 위한 봇입니다.
`,
      ...Markup.inlineKeyboard([
        [
          Markup.button.callback('📝 거래 신청', 'create_trade'),
          Markup.button.callback('📞 고객센터', 'support')
        ],
        [
          Markup.button.callback('📚 튜토리얼', 'tutorial'),
          Markup.button.callback('✅ 완료 거래', 'done')
        ]
      ])
    }
  )

})

bot.action('tutorial', async (ctx) => {

  await ctx.editMessageCaption(`
📚 튜토리얼 (1/2)

1️⃣ 거래 신청
2️⃣ 상대방 아이디 입력
3️⃣ 거래 진행
`, {
    reply_markup: {
      inline_keyboard: [
        [
          {
            text: '▶ 다음',
            callback_data: 'tutorial2'
          }
        ]
      ]
    }
  })

})

bot.action('tutorial2', async (ctx) => {

  await ctx.editMessageCaption(`
⚠️ 주의사항

❌ 외부 링크 클릭 금지
❌ 거래방 밖 송금 금지
✅ 문제 시 관리자 호출
`, {
    reply_markup: {
      inline_keyboard: [
        [
          {
            text: '⬅ 이전',
            callback_data: 'tutorial'
          }
        ]
      ]
    }
  })

})

bot.action('support', async (ctx) => {

  await ctx.reply(`
📞 고객센터

문의:
@네아이디
`)

})

bot.action('done', async (ctx) => {

  await ctx.reply(`
✅ 완료된 거래가 없습니다.
`)

})

bot.action('create_trade', async (ctx) => {

  const code = Math.random()
    .toString(36)
    .substring(2, 8)
    .toUpperCase()

  await ctx.reply(`
📝 거래가 생성되었습니다.

📋 거래코드:
${code}
`)

})

bot.launch()

console.log('봇 실행중...')
