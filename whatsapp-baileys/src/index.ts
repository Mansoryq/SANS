import express from 'express'
import pino from 'pino'
import { Pool } from 'pg'
import makeWASocket, { DisconnectReason } from '@whiskeysockets/baileys'
import { Boom } from '@hapi/boom'
import * as qrcode from 'qrcode-terminal'
import { usePgAuthState } from './auth.js'

const app = express()
app.use(express.json())

const port = process.env.PORT || 3000
const pgUrl = process.env.DATABASE_URL || 'postgres://postgres:postgres@localhost:5432/sans'

const pool = new Pool({
    connectionString: pgUrl,
    ssl: pgUrl.includes('supabase') ? { rejectUnauthorized: false } : false
})

let sock: any = null
let qrCodeString = ''

async function connectToWhatsApp() {
    const { state, saveCreds } = await usePgAuthState(pool, 'sans-bot')
    
    sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
        logger: pino({ level: 'silent' })
    })

    sock.ev.on('connection.update', (update: any) => {
        const { connection, lastDisconnect, qr } = update
        if (qr) {
            qrCodeString = qr
            qrcode.generate(qr, { small: true })
        }
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error as Boom)?.output?.statusCode !== DisconnectReason.loggedOut
            console.log('Connection closed due to ', lastDisconnect?.error, ', reconnecting ', shouldReconnect)
            if (shouldReconnect) {
                connectToWhatsApp()
            }
        } else if (connection === 'open') {
            console.log('WhatsApp connection opened!')
            qrCodeString = ''
        }
    })

    sock.ev.on('creds.update', saveCreds)
}

connectToWhatsApp().catch(console.error)

// REST API for Python Backend
app.get('/qr', (req, res) => {
    if (qrCodeString) {
        res.json({ qr: qrCodeString, status: 'waiting_for_scan' })
    } else if (sock?.user) {
        res.json({ status: 'connected', user: sock.user })
    } else {
        res.json({ status: 'connecting' })
    }
})

app.get('/status', (req, res) => {
    if (sock?.user) {
        res.json({ status: 'connected', user: sock.user })
    } else {
        res.json({ status: 'disconnected' })
    }
})

app.post('/send', async (req, res) => {
    try {
        const { phone, message } = req.body
        if (!phone || !message) {
            return res.status(400).json({ error: 'Missing phone or message' })
        }
        
        // WhatsApp format uses JID: number@s.whatsapp.net
        const jid = `${phone.replace(/\D/g, '')}@s.whatsapp.net`
        
        if (!sock?.user) {
            return res.status(503).json({ error: 'WhatsApp not connected' })
        }

        const [result] = await sock.onWhatsApp(jid)
        if (!result || !result.exists) {
            return res.status(404).json({ error: 'Number not on WhatsApp' })
        }
        
        await sock.sendMessage(result.jid, { text: message })
        res.json({ success: true, message: 'Message sent' })
        
    } catch (error: any) {
        console.error('Error sending message:', error)
        res.status(500).json({ error: error.message })
    }
})

app.listen(port, () => {
    console.log(`Baileys Microservice running on port ${port}`)
})
